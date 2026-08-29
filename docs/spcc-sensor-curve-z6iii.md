# SPCC sensor response for the Nikon Z6 III — deep dive

- **Question / scope** — every colour calibration this repo has shipped ran
  Siril SPCC with no sensor named, and every record says *"NO MATCHING SENSOR —
  siril's generic/default response was applied"*. This investigates (a) what
  SPCC actually integrates against when no sensor is named, (b) whether a
  Nikon Z6 III response curve exists anywhere and what would stand in for one,
  (c) how SPCC is wired in this chain and what a curve would change, and
  (d) the test that decides whether a curve is an improvement. It exists
  because a director's inspection reported a faint green excess in the
  brightest Milky Way band of the finals (background R/G 0.989, B/G 0.960
  against ~1.00 in the outer sky — untracked, see UNCHECKED) with the sensor
  default as a candidate cause.
- **Context** — 2026-08-28. Siril **1.4.4** (tag `e89421c`, 2026-06-17)
  as the system flatpak; `siril-spcc-database` clone at `3426f09`
  (2026-06-03, `--depth 1`); camera **NIKON Z6_3** with the **NIKKOR Z
  24-70mm f/4 S** at 70 mm, 2.5 s, ISO 1600 (`datasets/*/set-*/acquisition.json`);
  x86-64, CPU-only, headless. Written read-only during a running from-raws
  campaign: **no Siril was invoked** — every statement about the tool is a
  source read of tag 1.4.4 (cloned to the session scratchpad; upstream paths
  cited as `src/...`) or a read of the 48 SPCC logs on disk under
  `sessions/*/work/spcc_*.log`, plus the H0 probe record
  (`datasets/july31/set-01/qa_work/spcc_h0_probe.json`), which is the one
  Siril run this investigation cites. Evidence classes follow
  `docs/dead-ends/00-registry-contract.md`: **MEASURED** / **MECHANISM** /
  **DOCTRINE**, and every claim below carries one.

## 1. Findings

### 1.1 How SPCC models an OSC sensor (MECHANISM — source read, 1.4.4)

The whole model is a pointwise product on Gaia's 2 nm grid, integrated.

- **Grid.** `XPSAMPLED_LEN 343`, wavelengths 336–1020 nm step 2
  (`src/core/siril.h:614`, `src/algos/spcc.c:44`); integration bounds
  `XPSAMPLED_MIN_WL 337.0` / `MAX 1019.0` (`src/algos/spcc.h`). The local
  catalogue is the `xpsamp` chunks (`catalogue_gaia_photo`); each star arrives as
  its XP sampled spectrum.
- **Star → photon counts.** `flux_to_relcount()` multiplies each sample by its
  wavelength and normalises at sample 82 (`src/algos/spcc.c:97-105`).
- **Channel response** `get_spectrum_from_args()` (`src/algos/spcc.c:259-308`).
  OSC branch: the sensor's per-channel curve (Akima-interpolated onto the grid,
  **zero outside the JSON's wavelength range**) × the OSC filter (skipped in
  narrowband mode) × the DSLR LPF **only if the sensor object carries
  `is_dslr`** × the atmosphere model only with `-atmos`. Mono branch: mono
  sensor × the per-channel mono filter. Nothing else enters.
- **Expected flux per star and channel** = ∫ response × spectrum over 337–1019
  (`src/algos/photometric_cc.c:384-392`); the catalogue colours are the ratios
  `crg = R/G`, `cbg = B/G`. The image colours are aperture-photometry flux
  ratios per star (`10^(-0.4 mag)`, local annulus background; radii scaled from
  the image FWHM — "Photometry radii set to 7.9 for inner and 17.9 for outer" on
  july31/set-01).
- **White reference** — the selected `WB_REF` spectrum through the same three
  responses gives `wrg`, `wbg` (`photometric_cc.c:409-422`). Default name
  literal `"Average Spiral Galaxy"` (SWIRE template).
- **Fit and K** (`photometric_cc.c:463-494`): a Siegel **repeated-median** line
  per colour, `Image R/G = a + b·Catalog R/G`, then
  `kr = 1/(a + b·wrg)`, `kg = 1`, `kb = 1/(abg + bbg·wbg)`, normalised by the
  largest. **K is the fitted line evaluated at the white reference's catalogue
  colour.** The same K then scales every pixel of the channel, and the
  per-channel background offsets `B0..B2` neutralise the auto-selected sky
  reference (`-bgtol`, default −2.8/+2.0 σ).
- **Warnings** (`photometric_cc.c:568-571`): `< 20` stars → "may not be
  perfect"; else `deviation > 0.1` on either fit → *"seems to have found an
  imprecise solution, consider correcting the image gradient first"*. The
  deviation is the `sigma` printed on the fit line.
- **Two invariances that bound what a curve can do** (MECHANISM, derived
  from the lines above, not probed): (i) scaling one channel's curve by a
  constant scales that catalogue ratio for every star AND the white reference
  by the same constant; the fit's slope absorbs it and `a + b·w` is unchanged —
  **the product is invariant to per-channel normalisation of the curve** (so
  database entries normalised per channel, e.g. `Nikon_D500.json`, are harmless
  here); (ii) only the **shape** of each channel — how its integral of a star's
  spectrum varies with the star's colour — moves K, and it moves K through
  the fitted line's value at ONE colour (the white reference). A wrong shape
  therefore shows first in the fit's geometry (intercept, slope, sigma) and only
  second-order in K, when the white-reference colour sits inside the
  population the line was fitted through. That is why a "sensor swap moved K
  ≤1.5%" is expected even between badly mismatched curves, and why the K delta
  alone cannot grade a curve.
- **Nothing in the product records the sensor used.** The linear ICC source
  profile that would have named it is commented out in 1.4.4
  (`photometric_cc.c:882-887`, *"temporarily removed pending fixing the source
  profile calc"*). The only record is this repo's `spcc_<set>.json`.
- `-atmos` is a Rayleigh-only transmittance at one airmass (from `AIRMASS`,
  else `CENTALT`, else a fixed 41.9° zenith angle; `spcc.c:170-193`); not used by
  the chain and outside this item.

### 1.2 What actually ran on this rig — the "generic default" does not exist (MEASURED + MECHANISM)

**The premise in every record, the README stage table, TOOLS.md, the pipeline
doc and `spcc_run.py` — that with no name SPCC "fits against siril's default
response" — is false.** There is no default curve in the code path.

- `do_pcc()` (`src/core/command.c:9933-10214`) resolves names against the
  in-memory lists with `get_favourite_oscsensor()` /
  `get_favourite_spccobject()` (`src/gui/photometric_cc.c:648-676`). With no
  `-oscsensor=` it takes the **mono** branch when the persisted preference
  `photometry/is_mono` is true (compiled default TRUE, `settings.c:278`; this
  rig's `config.1.4.ini` line 69: `is_mono=true`, every `*pref=` empty,
  `oscfilterpref=No filter`, `is_dslr=false`). A name that matches nothing
  returns −1 and the command **errors**: *"Either the sensor or a filter was
  not specified as argument or guessable from previous use."* A `spcc` run
  never stores a name: `do_pcc` only reads `is_mono` (`command.c:9942`), the
  writers of every `*pref`/`is_mono`/`is_dslr` are the GUI combo and switch
  callbacks (`gui/photometric_cc.c:1059, 1400-1471`), and the config is
  rewritten after every headless script (`command_line_processor.c:404`)
  with the in-memory values unchanged — MECHANISM from source, MEASURED by
  H0's zero-change diff of `config.1.4.ini` lines 62-70 after each arm (only
  `wd=` moved).
- **But the lists are loaded AFTER the names are resolved** —
  `load_spcc_metadata_if_needed()` sits at `command.c:10205`, after the lookups
  at 10152–10188 — and both lookup helpers begin `if (!list) return 0;`. In
  `siril-cli` nothing loads the database at startup (the only callers are
  `do_pcc` itself, `process_spcc_list`, and the GUI combo population), so **in a
  fresh headless process every selection resolves to index 0 of a list that is
  then populated and byte-sorted** (`spcc_json.c:855-861`). The log line
  *"SPCC will use …"* prints the argument or preference string, not the entry
  chosen, so it cannot reveal this. Upstream `master` at `ee7b942` (2026-08-23)
  has the same order.
- **MEASURED on this rig — all 48 logs**: every one prints
  `SPCC will use mono senor "(null)" and filters "(null)", "(null)" and "(null)`
  and only THEN `SPCC JSON metadata loaded` (e.g.
  `sessions/july31/work/spcc_set-01_set-01_full.log:52-53`) — the order the
  mechanism predicts. Every K record in `datasets/*/*/qa_work/spcc_*.json` (54)
  plus `datasets/corpus/spcc_set-0b_*.json` carries `sensor_spec: null`.
- **The model every product was calibrated against** (index 0 of each list on
  the local clone, byte order of `name`): sensor **"Generic mono sensor"**
  (`mono_sensors/Generic_mono.json`, 81 points, 378–1000 nm, peak 0.91) ×
  filters **Antlia R / Antlia G / Antlia B** (`mono_filters/Antlia_LRGB-V_Pro.json`:
  584.6–716.3 / 480.7–582.8 / 412.1–531.5 nm — sharp-edged, non-overlapping
  mono RGB filters; the LUM object maps to `SPCC_INVIS` and is in no channel
  list, `spcc_json.c:166-185`) × white reference index 0 = **"Average Spiral
  Galaxy"** (first by byte order, so the intended default by luck). A Bayer
  camera was modelled as a mono CMOS behind a mono LRGB filter set.
- **Self-consistency (MEASURED, derived from the logs):** with K normalised
  to R, `a + b·wrg = K_G` and `abg + bbg·wbg = K_G/K_B`, so the white
  reference's catalogue colour under the model in force can be recovered from
  each log: across all 48 runs **wrg = 0.826–0.830, wbg = 0.983–0.986** — one
  identical response model behind every run, as the mechanism requires.
- **What the fits look like under that model (MEASURED, 48 logs):** the
  "imprecise solution" warning fired **48 of 48** times; R/G sigma 0.118–0.211
  (median 0.144), B/G 0.074–0.173 (median 0.098) against the 0.1 line. Slopes
  are 0.18–0.26 (R/G) and 0.46–0.60 (B/G) with intercepts 0.42–0.50 and
  0.15–0.31. A correct response gives a line through the origin
  (`Image = gain-ratio × Catalog`), so the **intercept's share of the K
  prediction, `a/(a + b·w)`** — computable from the log as `a/K_G` for R/G and
  `abg·K_B/K_G` for B/G — is a model-mismatch scalar: **0.66–0.77 (median
  0.71) for R/G and 0.20–0.40 (median 0.29) for B/G**. Under the index-0 model
  71% of the red K comes from the intercept. That is the signature of catalogue
  colours far more dispersed than the image's — sharp filters standing in for
  broad, overlapping Bayer dyes — and it is the tool's own number, not an
  in-house metric.
- **The named-sensor path is broken the same way.** With `-oscsensor=` given,
  the OSC branch runs, `get_favourite_oscsensor(NULL, name)` returns 0, and the
  run silently uses index 0 of the OSC lists: sensor **"Canon EOS 1D Mark III"**
  × OSC filter **"Antila RGB_ultra_ii"** (an `OSC_FILTER`-typed triband curve
  misfiled under `osc_sensors/`, listed as a filter because the loader keys on
  `type`) with `is_dslr` from the preference (false here, so no LPF) — while the
  log prints the name that was asked for. So a `recipe.json` `spcc` block, the
  fix every record's `sensor_match_note` prescribes, would change nothing and
  would make the record claim `named: <sensor>` for a run that used a Canon
  DSLR behind a triband filter. **MECHANISM, and still so after H0** — every
  named arm of the probe ran WITH the preload; the counterfactual (a named
  arm without `spcc_list`) has not been run (§5).
- **The tool-native cure is one line**: `spcc_list oscsensor` earlier in the
  same `.ssf` calls `load_spcc_metadata_if_needed()` (`command.c:11453`) and
  populates the lists for the life of the process; the subsequent `spcc` then
  matches names exactly (`g_strcmp0` on `model` for OSC sensors, `name` for
  everything else — `spcc_list` prints exactly those strings), and a null spec
  fails loudly instead of falling through. **MEASURED — H0, record
  `datasets/july31/set-01/qa_work/spcc_h0_probe.json`, logs
  `sessions/july31/work/h0_{null,d750,d500}.log`**, on the shipped
  `stack_set-01_full_wcs.fit` (PIPEREV 77e3a78), no `save`: with
  `spcc_list oscsensor` preceding `spcc`, `SPCC JSON metadata loaded` (log line
  52/56) precedes `SPCC will use OSC sensor "Nikon D750"` / `"Nikon D500"`
  (105/109 — the load line is printed by `spcc_list`; `spcc` prints no second
  one); both model strings appear verbatim in the `spcc_list` block (47 OSC
  sensors, no Z-body); **the two names give different K — D750 1.000/0.697/0.945,
  D500 1.000/0.700/0.955 (Δ −0.003/−0.010, above the 0.002 printed
  precision) — against the shipped index-0 run's 1.000/0.687/0.927 on the same
  input** (3077/5119 stars in all three); the spec-less arm exits 1 with
  Siril's own *"Either the sensor or a filter was not specified as argument or
  guessable from previous use"* and writes no K; the input's bytes and mtime
  and `git status` are unchanged after every arm. H0 PASS on all four
  clauses. The quoting form Siril's own `help spcc` documents and the probe
  used is the WHOLE token: `"-oscsensor=Nikon D750" "-oscfilter=No filter"
  "-whiteref=Average Spiral Galaxy"` — *"the entire argument must be enclosed
  in quotation marks"*. Two consequences of loading first (source read): a
  sensor flagged `is_dslr` then REQUIRES `-osclpf=` naming an existing LPF —
  the literal fallback `"Full spectrum"` matches no entry (the entry is
  `"Full spectrum (no filter)"`), the −1 check is gated on a flag not yet set,
  and the worker dereferences `g_list_nth(list, -1)` → NULL — a SIGSEGV of the
  exit-139 family; per entry on this clone (per-channel read of the JSON):
  `Nikon_D7200` carries `is_dslr: true` on its RED object, as do the ten SVO
  D-bodies, and the loader propagates a flag on any channel to all three
  (`spcc_json.c:248-261`); `Nikon_D750` and `Nikon_D500` carry none, which is
  why the probe could name them bare. And the mono/OSC branch is still decided
  by `is_mono` unless `-oscsensor=` is given.
- **H0's side reading — reported, not scored (the §4 bars are scored on the
  Z f arm and stand as written):** under either Nikon D-body curve the R/G fit
  moves toward the origin — `0.3265 + 0.6247·x` σ 0.095 (D750),
  `0.3484 + 0.5727·x` σ 0.093 (D500), against `0.4887 + 0.2395·x` σ 0.140 — an
  intercept share of 0.47/0.50 from 0.71 and a slope/K_G of 0.90/0.82 from
  0.35; the B/G fit does not — σ 0.107/0.108 against 0.110, intercept share
  0.42/0.38 against 0.39 — so the "imprecise solution" line still fires on
  B/G. The white-reference colour back-derived from the two arms moves as the
  response changes (R/G 0.593/0.614, B/G 0.706/0.709, against 0.828/0.985 under
  the index-0 model), the check §1.1(ii) requires.
- **The inherited "grounding is immaterial" number is UNCHECKED in subject.**
  The previous rig measured `-oscsensor "Sony IMX571" -oscfilter "Optolong
  L-Pro"` vs null on `siril-m8m20/lpro_180s`: K G 0.912→0.898 (−1.5%), R
  0.370→0.371, output p99 ≤2.6e-4 (commit `cf96f60`). Under 1.4.x's resolution
  order neither arm can have used the IMX571 curve in a fresh CLI process; the
  logs are not tracked and the dataset is off-disk, so which two curves were
  compared is unrecoverable (UNREPRODUCIBLE BY CONSTRUCTION in the registry's
  sense). It supports exactly one thing: two wrong models move K by ~1.5% —
  which §1.1(ii) predicts. It does not support "the null default is adequate".

### 1.3 The database — schema, loading, local install, upstream path (DOCTRINE + source read)

- **Location** is hard-coded: `g_get_user_data_dir()/siril-spcc-database`
  (`src/core/siril_app_dirs.c:161-163`) — under the flatpak
  `~/.var/app/org.siril.Siril/data/siril-spcc-database` (manifest row
  `spcc-database`, `scripts/setup/manifest.tsv:18`; bootstrap clones `--depth 1`).
- **Loading**: lazy, once per process; a recursive walk of every `*.json`
  under the root except `.git` and names containing `schema`
  (`spcc_json.c:734-766`); **no index, no schema validation in Siril** (the
  schema is enforced only by the repo's CI); a parse or field error logs in
  red and drops the file. `siril-cli` is a fresh process per `-s`, so **a file
  dropped anywhere under the clone is live on the next run, tracked or not**.
- **Format** (README + `spcc_json.c:42-227`): the root is an **array of
  objects**; required per object: `type` (`OSC_SENSOR` needs exactly three
  objects with identical `model` and `channel` RED/GREEN/BLUE), `model`,
  `name`, `manufacturer`, `dataSource`, `dataQualityMarker` (1–5), `version`,
  `wavelength: {value[], units: nm|micrometer|angstrom|m}`,
  `values: {value[], range}`; optional `comment`, `is_dslr`. Values are "QE"
  for sensors and transmittance for filters, any scale via `range`; 5–2000
  points, monotonic, duplicates removed with a warning. `dataQualityMarker`
  is display-only — the calculation never reads it.
- **`auto_update_spcc`** is GUI-only (`gui/callbacks.c:1636`; `main-cli.c`
  runs none of it): fetch + `git reset --hard FETCH_HEAD` on the tracked
  files, remote URL must be exactly upstream, a non-git directory is deleted
  and re-cloned. This rig pins `auto_update_spcc=false`, `use_spcc_repository=true`.
  A hard reset reverts edits to tracked files and leaves untracked files —
  so a local entry survives as a NEW file, never as an edit of an upstream one.
- **Upstream contribution**: one MR per dataset with the plot attached
  (`.gitlab/merge_request_templates/default.md`); WebPlotDigitizer → CSV →
  `utils/process_osc_sensor.py --manufacturer --model --dataSource` →
  `utils/visualize.py`; CI runs `ajv` + `remove_duplicates.py`. Quality
  markers: 1 unknown provenance (rejected), 2 scanned from a plot, 3 OEM
  tabulated / academic, 4 OEM ≤2 nm tabulated, 5 personally calibrated
  ("never given to repository files"). Repository licence **GPLv3**
  (`LICENSE.md`). Nikon-related upstream history: `!109` D750 (merged
  2026-06, HdM Stuttgart open-film-tools slit/grating data), `!81` D500 (merged
  2025-12, digitised from a dpreview plot), `!54` D7200 (merged
  2025-07/08, nikongear plot); the ten SVO-sourced D-bodies + `Cameras_Nikon.*_Block`
  LPFs; issue #3 *"Add new sensors"* (a Siril developer, open) points
  contributors at `rawtoaces` and `butcherg/ssf-data`; issue #4 (closed)
  raised per-channel relative normalisation — harmless per §1.1(i). The
  Siril lead developer's stated policy (pixls.us threads 50560, 56806, 55670):
  users add sensors themselves via MR.
- **The Siril docs' own guidance** (DOCTRINE,
  https://siril.readthedocs.io/en/stable/processing/color-calibration/spcc.html):
  *"Don't worry if there isn't an exact match for your equipment, just pick
  the closest option, or the appropriate default option"*; on DSLR LPFs:
  *"select any of the Canon or Nikon low-pass filters: the effect is very
  minor"*; command reference: *"If one of the spectral data argument is
  omitted, the previously used value will be used."* No quantified
  sensitivity to the sensor choice exists in the docs, the issue tracker or
  the forums searched (NOT FOUND).

### 1.4 Does a Z6 III curve exist? (DOCTRINE — sources in §2; the premises are in §5)

**No.** Nothing measured for the Z6 III, the Z6 II, the Z8 or the Z9 was found
in any open collection (NOT FOUND — searched: the Siril database and its MR
list, PixInsight's documented list, SVO's "Cameras" facility, camspec/Jiang
2013, the Zhao/Kawakami database, Darrodi/NPL, SPECTACLE, ASWF
`rawtoaces-data`/Weta physlight, Butcher `ssf-data`, Buil, Kolari, maxmax,
beyondvisible, the DPReview/CN/SGL threads reachable). What does exist:

- **Local clone (`3426f09`):** 47 OSC sensors — 13 Nikon D-bodies (D200, D3,
  D300s, D3X, D40, D50, D5100, D700, D80, D90 relayed by SVO from the camspec
  monochromator set, 4000–7200 Å at 100 Å, per-channel normalised; D500 from a
  dpreview homemade-spectrometer plot; D7200 from a nikongear plot; D750 from
  HdM Stuttgart's open-film-tools), 9 Canon EOS, Sony IMX071…IMX715 (the
  **IMX410** entry is ZWO's ASI2400MC plot — a bare sensor with **87% red
  response at 656 nm** where every stock Nikon body measures 25–30%, and its
  three objects are mis-named "Sony IMX183 Red/Green/Blue"), Fujifilm X-Trans
  5 HR, Samsung ISOCELL, ZWO Seestars. **No Z-series body.** `spcc_list
  oscsensor` lists these `model` strings (H0 measured 47). `is_dslr`, read per
  channel: the ten SVO D-bodies and `Nikon_D7200` carry `true` on their RED
  object — the loader propagates any channel's flag to all three — while
  `Nikon_D750` and `Nikon_D500` carry none.
- **The one professionally measured 2020s Nikon full-frame Bayer body: the
  Nikon Z f**, in ASWF `rawtoaces-data` (`data/camera/Nikon_Z_f_380_780_5.json`,
  from Weta Digital's physlight release, commit `cf6452c` 2025-09-15):
  380–780 nm at 5 nm, units "relative", measured on Weta's "lightsaber" rig
  (the rig is named, the method is not documented), **Apache-2.0** — which the
  GPLv3 database can carry, and which the database's own issue #3 (*"Add new
  sensors"*, a Siril developer) names as a source to mine. The same batch holds
  Nikon D3300/D5300/D810/D850, Sony α7 III (the IMX410 in a Sony body),
  Canon R/RP/R5/R6, Fujifilm — 52 bodies.
- **Three DIY measurements of the original Z6** (all grating-on-a-slit,
  relative): **Butcher `ssf-data`** — `Nikon/Z6/spectroscope/Nikon_Z6_ssf.csv`,
  Nikon Z 6 with the **NIKKOR Z 24-70mm f/4 S — this project's lens model**,
  transmissive ruled grating, single image, 2020-08-27, 400–715 nm at 5 nm, 64
  rows, two-decimal values, globally normalised (B 1.00 at 465 nm, G 0.97 at
  530, R 0.65 at 595, R down to 0.04 by 675 nm — the body's IR-cut is inside),
  lamp power compensation against a reference file whose provenance is
  unstated, CC BY-NC-SA 4.0; Shelley (sunlit target, cardboard slit, relative
  only, "25% higher response at H-alpha than the EOS R"); Delley (DPReview,
  tungsten-halogen through a grating: "sharp lower cutoff at about 420nm …
  peter-out … about 670nm" — page blocked, snippet only).
- **The Nikon dye family is tight across a decade** (agent-derived from the
  published curves, INFERRED): Z f / D850 / D810 / D5300 (Weta) and D200
  (camspec) all peak red at 590 nm with FWHM 52–58 nm and pass 25–30% of the
  red peak at 655 nm; Canon bodies run FWHM 68–75 nm and 34–35%. Butcher's
  Z6 sits in the Nikon family (peak 595, 28% at 655). So a Nikon Z proxy is
  a family match; what it cannot certify is the Z6 III's own hot mirror and
  dye lot (§1.4a).

#### 1.4a Sensor identity (DOCTRINE — cited; every "shares" below is a premise, §5)

- **The Z6 III sensor is the Sony IMX820AQJ**, extracted from a Z6 III by
  TechInsights: 24.5 MP FX, *"partially stacked back-illuminated rolling
  shutter"*, 5.9 µm pitch. Sony's own product table lists **IMX820** (35 mm,
  24 M, 5.94 µm, 65 fps, technology "CoW BI", flagged New) beside **IMX410**
  (24 M, 5.94 µm, 19 fps, "BI"). Nikon's release: *"the first mirrorless camera
  to adopt this new sensor architecture … approximately 3.5x increase to
  readout speed compared to the previous-generation Z6II"*. CFA: Bayer
  (DPReview spec sheet); NEF 14-bit (Nikon).
- **The Z6 II uses the Z6's sensor** (Wikipedia; DXOMARK: *"retains the core
  spec of the original, such as the 24.5 MP BSI CMOS sensor"*); that the Z6 is
  an IMX410 variant is community consensus with **no teardown found**
  (TechInsights' IMX410 report is of the Sony α7 III). The **Z f** is
  *"believed to use the same 24.5MP BSI-CMOS sensor used in the Nikon Z6II"*
  (Wikipedia). The Z9 is the IMX609AQJ (TechInsights via Wikipedia).
- **So no available curve shares the Z6 III's die.** The Z f and Z6 proxies
  share the IMX410-class die with each other, not with the IMX820; what a
  proxy can share with the Z6 III is Nikon's CFA dye set and hot-mirror
  generation — plausible (the family in §1.4) and **measured by no one**.
- **Filter stack:** the Z6's is a 0.3 mm dust-reduction glass over a 0.8 mm
  UV/IR-cut (Kolari teardown); the Z6 III's stack is undescribed in the
  reachable teardown (Kolari sells a full-spectrum conversion for it, so a
  stock hot mirror is implied). Hot-mirror transmission at 656 nm varies by
  Nikon generation (Kolari via Clarkvision: D90 a few percent vs D80 over
  20%) — the single largest unknown a Nikon-family proxy carries for this body.

### 1.5 Options, each with its evidence class and cost

| # | Option | What it is | Deviation / risk | Cost | Class |
|---|---|---|---|---|---|
| 0 | **Fix the runner** (prerequisite to everything) | `spcc_list oscsensor` before `spcc` in the generated `.ssf`; assert in the log that `SPCC JSON metadata loaded` precedes `SPCC will use` AND that the requested model string appears verbatim in the `spcc_list` block; require a named `-oscsensor` (a null spec then fails loudly, as Siril intends); pass `"-oscfilter=No filter"` and `"-whiteref=Average Spiral Galaxy"` explicitly, whole-token quoted as Siril's `help spcc` states; refuse `is_dslr` entries (read from the JSON objects, not the model name) unless `-osclpf=` names an existing LPF | none — it makes the tool do what its docs say; the record's `sensor_match` becomes true | ~20 lines in `spcc_run.py` | MEASURED by H0 for the preload + name path (§1.2); the counterfactual — a named arm without the preload — unrun |
| A1 | **Proxy: Nikon Z f (Weta / ASWF `rawtoaces-data`)** converted to a local `osc_sensors/Nikon_Zf.json` (three objects, `model "Nikon Z f"`, no `is_dslr`, marker 3 — professionally measured, tabulated, 5 nm — `dataSource` the ASWF URL + Zenodo DOI) | the newest professionally measured Nikon full-frame Bayer body, body filters inside, 380–780 nm, Apache-2.0 → **contributable upstream** | a different die (IMX410-class vs IMX820); Nikon dye/hot-mirror continuity assumed; "lightsaber" method undocumented; "relative" undefined (QE vs responsivity — §1.6) | ~30 min conversion with `utils/process_osc_sensor.py`; machine-local file fetched by the bootstrap; an upstream MR after the §4 test | DOCTRINE (proxy) → MEASURED by §4 |
| A1′ | **Proxy: Nikon Z6 (Butcher)** as `Nikon_Z6.json`, marker 2 | the nearest Z-body by name, **through this project's lens model** | DIY grating, 400–715 nm, two-decimal values, unstated lamp calibration; CC BY-NC-SA — fine to use locally, **not** redistributable inside a GPLv3 database without the author | ~30 min; local only | DOCTRINE → MEASURED by §4 |
| A2 | **Proxy: Nikon D750** (in the database) | slit/grating measurement at HdM Stuttgart, 360–830 nm at 1 nm, marker 3, inter-channel scale intact | 2014 DSLR; earlier dye and hot-mirror generation | zero | DOCTRINE |
| A3 | Sony IMX410 (in the database) | the Z6/Z f-class die as an astro camera | **unusable for a stock body**: no hot mirror (87% at 656 nm vs 25–30% real); mis-named objects | — | rejected on the numbers |
| B1 | **Measure this system** — objective grating on an A0V star | a transmission grating (Star Analyser SA-100 $225 / SA-200 $244, or grating film) in front of the 24-70 at 70 mm; Vega (CALSPEC `alpha_lyr_stis_012`, 0.5% absolute at 5556 Å) or a MILES standard near the same altitude; extract with an official spectroscopy tool (ISIS / BASS Project / RSpec / specINTI); divide by the reference and a Rayleigh + aerosol extinction model → body + lens + hot mirror + CFA + silicon, the thing SPCC wants; marker 5 for this rig; an upstream **"Nikon Z6 III"** entry (marker 2–3 as a third-party measurement) | the grating's first-order efficiency is inside the result (SA-100: ~60% at 400, ~80% at 500–550, ~70% at 700 nm — Pieri) and must be divided out; second order above ~800 nm (irrelevant behind a hot mirror); Balmer lines and telluric bands to interpolate across; a trailed spectrum on the fixed mount — many short subs | ~$250; one clear night; a few hours' reduction; the field's accuracy: a few percent after smoothing (Buil), 3.5–5.8% for the uncalibrated-grating + closed-form method (Makabe 2025) | DOCTRINE → MEASURED |
| B2 | **Measure this system** — slit spectroscope on a lamp (`ssftool` method; Pieri's sun-on-white-paper variant) | indoors; CFL lines for wavelength; a broadband lamp for power | the source spectrum must be KNOWN: with a SMARTS2 solar model the grating route reached RMS 0.02–0.04 against a monochromator, with a black-body assumption 0.10–0.12 (Burggraaff 2019) — the reference spectrum dominates the error | $50–100, a day | DOCTRINE |
| B3 | Monochromator + integrating sphere + calibrated photodiode | the gold standard behind camspec, NPL, SPECTACLE (RMS ≤0.005) | not reachable here (used 1/8 m monochromators trade at hundreds to thousands USD; a NIST-traceable photodiode on top) | — | — |
| C | **Data-derived curve** from this project's star photometry vs Gaia XP | fit response shapes so that image colours match synthetic colours | **FORBIDDEN as a calibration** — it reads the deliverable's pixels to derive the instrument that then calibrates them (the bright line's independence rule), it is circular with SPCC's own fit (any curve fitted from these stars straightens these stars), and it is ill-posed by theorem (§1.6: photometry constrains only the projection onto the calibrators' SEDs; Gaia's own work resolved 3–5 basis functions from 100–200 CALSPEC-class spectra; the professional per-image analogue holds the detector shape fixed). As a **diagnostic** it is unnecessary: SPCC's own logged fit already reports the shape mismatch (§1.2) | — | out of bounds |

**One recommendation.** Do 0, then **A1 (Nikon Z f, Weta)** under the
pre-registered test in §4, with A1′ (Butcher Z6) and A2 (D750) run in the
same session as control arms — they are the positive control that names are
honoured, and the second and third opinions on whether the fit geometry is
curve-driven at all. B1 is the standards-grade endpoint and the only route
to a true Z6 III entry; it is a separate, owner-gated capture (a grating,
one night) and is NOT required to retire the index-0 accident, which 0 alone
does. Reasons for A1 over A1′: a professional rig against a DIY one, 380–780
against 400–715, tabulated precision against two decimals, a 2023 body
against a 2018 one, and a licence that lets the curve go upstream as the
first Nikon Z entry — which is how a proxy stops being this repo's private
deviation. Reason A1′ stays in the test rather than being dropped: it is the
only curve taken through this project's lens model, so if A1 and A1′
disagree on the fit geometry the lens is a suspect, and if they agree the
proxy family is confirmed twice. Reason against "just pick any": §1.1(ii) —
the K delta between two wrong curves is small by construction, so the choice
is graded by the fit geometry, not by how little K moves.

### 1.6 Standards-first — what the industry does for OSC colour calibration

The reference implementation is PixInsight's SpectrophotometricColorCalibration
(SPCC, Peris & Conejero, Nov 2022), which Siril's SPCC reproduces (DOCTRINE —
the PixInsight documentation, https://pixinsight.com/doc/docs/SPCC/SPCC.html,
and Siril's).

- **Same model, same output.** Three filter curves × an optional QE curve
  (*"by default, it is an ideal QE curve with a constant value equal to 1
  … For color sensors and cameras, one assumes that quantum efficiency is
  being taken into account implicitly by the corresponding filter spectral
  response curves"*); each Gaia DR3 sampled spectrum (336–1020 nm) is
  multiplied and integrated; **two robust repeated-median lines** of image
  ratio vs catalogue ratio; the white reference pushed through them gives
  **three multiplicative factors**. The fitted quantity is 2 slopes + 2
  intercepts; the product is 3 scalars — identical in kind to Siril's §1.1.
- **Where its sensor curves come from.** An XML database (`filters.xspd`)
  shipping *"Astrodon E and I series. Astronomik. Baader. Chroma. Selected
  models of Canon, Nikon and Pentax DSLRs. A generic Sony color image sensor
  with three options (… UV-cut … UV and IR-cut). Astronomical standard
  photometric filter sets"*. **Its default OSC curve is "a generic Sony
  color image sensor"** (`Sony Color Sensor R-UVIRcut` is the doc's own CSV
  example, 400–700 nm at 2 nm), i.e. the industry default for an unlisted
  OSC is a real, measured-class Bayer curve of a modern Sony sensor — not a
  mono chip behind mono filters. Users add curves by CSV import
  (`type,"filter"` / `name` / `wavelength` nm / `transmission` 0–1 /
  `channel` / `reference`) through Filter Management, and the lead developer's
  documented route is Curve Explorer → export XML → point Preferences at the
  file. No Nikon mirrorless body was found in its list (NOT FOUND — the list
  is not published outside the application).
- **What the reference says when your camera is not listed:** *"Even in this
  case, we recommend using SPCC over PCC, since by selecting an ideal QE curve
  and similar filters to yours it will calibrate your color image with much
  less uncertainty than PCC"*; on the QE curve: *"not a decisive parameter …
  by not setting your QE curve, you're not going to ruin your color
  calibration, in general"*; and it lists *"deficient filter characterization,
  deficient quantum efficiency curve characterization"* among the causes of
  outliers in the fits — which is the diagnostic §4 H1 reads. Experienced
  users on the PixInsight forum: *"The OSC RGB filters have very little
  difference (if any) between sensor manufacturers"* and *"look at the SPCC
  balance plots and ask yourself how much difference it is going to make"*
  (thread 24489). No developer of either tool quantifies the sensitivity
  (NOT FOUND).
- **The white reference is the same standard**: "Average spiral galaxy" —
  since Nov 2022 the mean of the S0–Sdm SWIRE templates ("very similar to
  … Sc"); Siril's `Average Spiral Galaxy` is the SWIRE template *"in a manner
  consistent with other astrophotography software providing the same white
  reference"* (Siril docs).
- **The open DSLR curves are one dataset.** The DSLR entries in Siril's
  database and (INFERRED) PixInsight's "selected models" trace to Jiang, Liu,
  Gu & Süsstrunk 2013 (WACV; https://zenodo.org/records/3245883 — a
  monochromator + integrating sphere + PR655 spectroradiometer, 400–720 nm at
  10 nm, 28 cameras incl. Nikon D3/D3X/D40/D50/D80/D90/D200/D300s/D700/D5100,
  CC BY-NC-SA), republished by the SVO Filter Profile Service's "Cameras"
  family — the Canon 600D values are digit-for-digit identical between
  Jiang's `camspec_database.txt` and `Canon_EOS600D.json`. So "Nikon" in
  either tool means a 2013 lab measurement of a 2005–2011 DSLR, lens-less.
- **Two conventions the field trips on, both relevant to a converted curve:**
  (a) *QE vs responsivity* — a "relative spectral response" plot from a
  camera vendor, a monochromator scan referenced to a power meter, or a
  grating measurement compensated *"to the measured illumination power"*
  (`ssftool`) is energy-based responsivity; Siril multiplies the Gaia flux by
  λ to get photon counts and treats the curve as QE, so an energy-based curve
  must be divided by λ (and renormalised) before it is a QE-like curve
  (PixInsight forum 24489 documents the trap; Siril's developers have not
  answered the same question in pixls thread 55670). The tilt is ≈ λ across
  each channel's band (~15–20% end to end), a within-channel shape change of
  exactly the kind §1.1(ii) says K is second-order to — but the convention is
  stated and applied consistently across the arms of §4, or the arms are not
  comparable. (b) *Per-channel normalisation* — harmless, §1.1(i).
- **The amateur DSLR photometry standard is transformation, not curves**
  (AAVSO DSLR Observing Manual v1.4 §6.4–6.5: per-setup coefficients
  `Tb_bv, Tv_bv, Tr_bv, Tbv` from a standard field; *"Transformation
  coefficients are for that particular setup only"*). SPCC's three scalars
  are that idea with Gaia XP as the standard field; a response *curve* is
  what lets the scalars be fitted through the right model, and the field's
  own gold standard for the curve is a monochromator (Burggraaff et al. 2019,
  Opt. Express 27, 19075 — NIST-traceable, RMS ≤0.005), with a grating on a
  known source as the accessible route (Buil's instrument-response method;
  Pieri's SA-100 recipe; Kloppenborg, Pieri et al. 2012 measured a DSLR's
  Bayer channels that way; Makabe et al. 2025 reach 3.5–5.8% with an
  uncalibrated grating sheet and closed-form efficiency solving).
- **Data-derived curves have a theorem against them.** Weiler et al. 2018
  (*Passband reconstruction from photometry*): photometry of calibrators
  constrains only the projection of the passband onto the span of their SEDs
  — *"the orthogonal component is fully unconstrained by the calibration
  sources … This component can only be guessed"* — and Gaia's own passband
  work, with 100–200 CALSPEC/NGSL-class spectra spanning O–M, resolved
  **M = 3–5 basis functions**. The closest professional analogue that fits
  a transmission per image against Gaia XP (Garrappa, Ofek et al. 2025)
  **holds the detector's shape fixed from the lab** and frees one peak-shift
  parameter plus two atmospheric scalars. With XP's own systematics (±2%
  above 400 nm; colour-dependent errors up to 50% below 400 nm; a BP/RP
  junction feature at 640–680 nm; Montegriffo et al. 2023, Huang et al. 2024),
  a Milky Way field of F–K stars identifies at most a low-order correction
  to a prior curve — which is what SPCC's three scalars already are. This is
  the standards-side reason option C is closed, on top of the bright-line
  reason in §1.5.

### 1.7 Audit — SPCC end to end in this repo (read-only; what is measured vs assumed)

- **Call chain.** `finish_render.sh` (solve → cone → SPCC → linked
  autostretch → 16-bit PNG) requires `--session`/`--set` (line 61) and, for a
  composite (`NMEMBER>1`), refuses a `--set` that is neither in the header's
  `CALSETS` window nor the `REGREF` set (lines 71–99, header-only) — routing
  is by a CONTRIBUTING set. It calls
  `spcc_run.py <session> <set> --in=<stack>_wcs.fit --out=<stack>_spcc.fit --tag=<name>`
  (line 217). `spcc_run.py` resolves the spec **CLI > `recipe.json` `spcc`
  block > none** (`resolve_spec`), writes `work/spcc_<set><tag>.gen.ssf` =
  `requires 1.4.0 / setcompress 0 / setext fit / set32bits / load / spcc
  -catalog=localgaia[ -oscsensor=… -oscfilter=… -whiteref=…] / save / close`,
  runs it through the serialized invoker (`scripts/lib/siril_run.py`), parses
  `K0..K2`, `B0..B2`, the photometry count and the excluded counts by regex,
  and writes `datasets/<session>/<set>/qa_work/spcc_<set>_<tag>.json` with
  `sensor_spec`, `sensor_spec_source`, `sensor_match`, `sensor_match_note`,
  `k_factors`, `b_offsets`, `n_photometry`, `n_kept`, input identity. The
  siril log stays in `<session>/work/`. MEASURED: on july31/set-01 the parse
  reproduces the log (5119 − 1943 outside − 99 failed = 3077 = Siril's own
  "using 3077 stars").
- **No `recipe.json` carries a `spcc` block today** (grep of every tracked
  recipe) — so every run went through the null path, and, per §1.2, a block
  would not have changed the curve.
- **What the records say vs what happened.** `sensor_match` = "NO MATCHING
  SENSOR — siril's generic/default response was applied" and the note "K
  factors calibrate against a DEFAULT response curve" are **false in
  substance**: the response was Generic-mono × Antlia RGB. The same wording
  lives in `README.md` stage 3 ("COMPLIANT, with ONE stated sensor
  limitation … sensor-null generic curve"), `TOOLS.md`, the pipeline doc §7 and
  its stop list, `finish_render.sh:36` ("the sp168 precedent"),
  `readiness_report.py` (YELLOW "sensor-null generic curve"), and
  `datasets/corpus/corpus4_build_record.json` `spcc_sensor`. These are sites
  to sweep when the item lands, not this document's to edit.
- **Consumers of the SPCC product.** `stack_<…>_spcc.fit` is the linear
  product the render tier consumes (`render_tier.sh <linear-spcc-stack.fit>`),
  the judge surface is stretched from it (`*_spcc-linked.png`), and **every
  one of the 13 tracked baselines is seeded on a `_spcc` product**
  (`baseline.json` → `measures.stack = …_spcc.fit`; `run_set_chain.sh:801`
  `BASEPROD=$RESULTS/stack_${NAME}_spcc.fit`). The guard reads only the
  `STACKNRM` header and re-measures corner spread, edge dipole and
  per-channel centre medians with Siril `stat` (tolerance
  `centre_median_max_frac_change 0.25`; level rows ADVISORY while `STACKNRM`
  differs). Present on disk after the rig cleanup (`06e5622`): 22 `_spcc.fit`, 22 judge
  PNGs — the canonical products; 55 tracked K records.
- **What a curve changes and what re-baselining it implies.** A curve
  changes exactly six numbers per product — K_R,K_G,K_B and B0..B2 — applied
  globally, so every `_spcc.fit`, every judge PNG and every render-tier output
  moves by a per-channel scale + offset; structure measures (corner spread,
  edge dipole — within-channel ratios) are invariant to the scale and move
  only by the offset; the centre-median rows move by ΔK (expected ≲5%,
  inside the 25% tolerance). So the guard is not expected to fire, but the
  README's acceptance rule ("any render the change alters is a declared
  delta … then re-baseline and tag") applies to all 13 baselines, the same
  shape as the zero-point item's stage 4 (closed; `docs/dead-ends/stacking-compose.md`). A curve landing is a
  BUILD-PATH change for the finish stage only (no member or compose rebuild;
  `PIPEREV` stamps on members/composites are unaffected; `_spcc` products
  carry none).
- **Measured vs assumed in this audit.** MEASURED: the 48 log lines, the 55
  records, the recipe grep, the parse identity, the config values, the
  baseline targets. Source-read MECHANISM: the resolution order and index-0
  fallback, the named-path failure, the `is_dslr` LPF crash, `spcc_list` as
  the cure. ASSUMED (untested): that the flatpak's 1.4.4 binary matches tag
  `1.4.4` line for line (the binary's strings match every message quoted;
  the tag is the flatpak's stated version).

### 1.8 The green excess — where the curve sits among the candidates (UNCHECKED)

The director's numbers (band R/G 0.989, B/G 0.960; outer sky ~1.00) are not
in any tracked record and were not re-measured here. What the mechanism
allows: a curve reaches the band ONLY through K (a global per-channel
scale) and the B offsets (a global per-channel constant), so **the curve can
shift the band's colour relative to the neutralised sky by exactly ΔK_R/ΔK_G
and ΔK_B/ΔK_G and nothing else** — a 1–4% green excess is inside the K
uncertainty a wrong shape leaves (§1.1(ii)), so the curve is a live but
second-order candidate. Two alternatives are at least as strong and are
distinguishable: (a) the OI 557.7 nm airglow line brightens toward the
horizon (van Rhijn), so across a 28.6° field the sky's own colour is not one
constant — a single per-channel offset neutralises the reference region and
leaves a green gradient wherever the band sits at a different altitude than
the reference boxes; discriminator: the band-vs-sky ratio measured at matched
altitude, or on two nights with the band at different altitudes; (b) the
flatless route's per-set sky flat converges to `sky × V` and the object's
own light is in the flat (BACKLOG `removal-conditions`, the sky-flat row): a
band that is redder than the sky in the flat divides the band's red down in
every light — a per-channel, band-shaped effect; discriminator: the master
flat's own R/G, B/G at the band position against the field. Neither is this
item's to settle; both are named so the §4 verdict is not over-read.

## 2. Sources

**Siril (source and docs, tag 1.4.4 unless noted)**
- `src/core/command.c` `do_pcc` 9933–10214 (name resolution 10151–10188, metadata load 10205; `process_spcc_list` 11449), `src/core/command_list.h:241-242` (syntax), `src/core/settings.c:268-290, 408-420` (`photometry/*pref`, `is_mono` default TRUE, `is_dslr`), `src/gui/photometric_cc.c:648-676` (`get_favourite_*`: `if (!list) return 0`), `src/algos/spcc.c` (grid, `flux_to_relcount`, `get_spectrum_from_args`, atmosphere), `src/algos/photometric_cc.c:296-571` (photometry, integration, repeated-median fits, K, warnings; ICC profile disabled 882–887), `src/io/spcc_json.c` (loader, channel bits 166–185, directory walk 734–766, sorts 855–861), `src/core/siril_app_dirs.c:161-163` (hard-coded path), `src/io/siril_git.c` + `src/gui/callbacks.c:1636` (GUI-only fetch + hard reset) — https://gitlab.com/free-astro/siril/-/tree/1.4.4 ; master `ee7b942` (2026-08-23) same order.
- SPCC documentation: https://siril.readthedocs.io/en/stable/processing/color-calibration/spcc.html ; command reference `spcc` / `spcc_list`.
- Siril lead developer on additions (pixls.us 50560, 56806, 55670); pyscript quoting thread 54615 (a different mechanism: unescaped quotes).
- The 48 logs `sessions/{july31,aug06,aug09,aug14}/work/spcc_*.log`; the H0 probe: record `datasets/july31/set-01/qa_work/spcc_h0_probe.json`, logs and scripts `sessions/july31/work/h0_{help,null,d750,d500}.{log,ssf}`, `h0_config_before.ini`; the 55 records `datasets/*/*/qa_work/spcc_*.json`, `datasets/corpus/spcc_set-0b_*.json`; `~/.var/app/org.siril.Siril/config/siril/config.1.4.ini` lines 22–23, 62–70, 158–160; commit `cf96f60` (the previous rig's grounding measurement).

**siril-spcc-database** (clone `3426f09`, https://gitlab.com/free-astro/siril-spcc-database)
- `README.md`, `spcc-database-schema.json`, `utils/README.md`, `utils/process_osc_sensor.py`, `svo-converter.py`, `LICENSE.md` (GPLv3); MRs !109 (D750), !81 (D500), !54 (D7200), !72 (Canon EOS R, open); issues #2, #3 (*"Add new sensors"* → rawtoaces, butcherg/ssf-data), #4 (relative QE); submission wizard https://siril-contrib-doc.readthedocs.io/en/latest/SPCCDatabase.html.

**Measured camera responses**
- Butcher, G., `ssf-data` — https://github.com/butcherg/ssf-data (`Nikon/Z6/spectroscope/{Nikon_Z6_ssf.csv,Nikon_Z6_ssf.json,README.md}`: Nikon Z 6 + NIKKOR Z 24-70mm f/4 S, transmissive ruled grating, single image, 2020-08-27, 400–715 nm at 5 nm; CC BY-NC-SA 4.0); `ssftool` — https://github.com/butcherg/ssftool (slit + grating, CFL lines for wavelength, `powercalibrate` against a supplied lamp power file, output normalised 0–1). Nikon bodies present: D200, D3, D300s, D3500, D3X, D40, D50, D5100, D700, D7000, D750, D80, D800, D90, Z6.
- Jiang, Liu, Gu, Süsstrunk 2013, *What is the space of spectral sensitivity functions for digital color cameras?*, WACV — https://zenodo.org/records/3245883 ; https://www.gujinwei.org/research/camspec/camspec_database.txt ; SVO "Cameras" family http://svo2.cab.inta-csic.es/svo/theory/fps/index.php?mode=browse&gname=Cameras.
- HdM Stuttgart open-film-tools camera responsivities (the D750 entry) — https://hdm-stuttgart.de/open-film-tools/english/camera_responsivities/.
- Darrodi, Finlayson, Goodman, Mackiewicz 2015, JOSA A 32, 381 (NPL ground truth for the Nikon D5100; chart-estimation methods "not sufficiently accurate").
- Burggraaff et al. 2019, Opt. Express 27, 19075 — https://arxiv.org/abs/1906.04155 (double monochromator, NIST-traceable; grating vs monochromator RMS 0.02–0.04 with a solar model, 0.10–0.12 with a black-body reference).
- Buil, C., instrument response — https://buil.astrosurf.com/instrument_response_us/ ; Canon 10D/5D/20D/350D/40D/50D pages (https://buil.astrosurf.com/us/digit/spectra.htm, http://www.astrosurf.com/buil/5d/test.htm, http://www.astrosurf.com/buil/50d/test.htm — "+/-15%" absolute QE).
- Pieri, R., SA-100 DSLR response recipe and SA-100 efficiency (~80% at 500–550 nm, ~60% at 400, ~70% at 700) — https://www.aavso.org/filter-response-curves ; Kloppenborg, Pieri et al. 2012, JAAVSO 40, 815 — https://arxiv.org/abs/1303.6870 ; Leadbeater on MILES standards and extinction — https://www.aavso.org/suitable-calibration-targets.
- Makabe et al. 2025 (ICCV), grating sheet + LED, 3.5–5.8% — https://arxiv.org/abs/2508.00330.
- Star Analyser SA-100 ($225) / SA-200 ($244) — https://rspec-astro.com/star-analyser/ ; CALSPEC Vega `alpha_lyr_stis_012` — https://www.stsci.edu/hst/instrumentation/reference-data-for-calibration-and-tools/astronomical-catalogs/calspec.

**PixInsight SPCC (the reference implementation)**
- Documentation — https://pixinsight.com/doc/docs/SPCC/SPCC.html ; release thread https://pixinsight.com/forum/index.php?threads/new-tool-released-spectrophotometriccolorcalibration-spcc.19599/ ; custom filters https://pixinsight.com/forum/index.php?threads/spcc-filters-file.21445/ ; sensor choice https://pixinsight.com/forum/index.php?threads/what-sensor-to-choose-in-spcc.22617/ ; QE vs responsivity https://pixinsight.com/forum/index.php?threads/spcc-filter-curves.24489/.

**Gaia XP and passband reconstruction**
- Gaia Collaboration, Montegriffo et al. 2023, A&A 674, A33 (synthetic photometry) — https://arxiv.org/abs/2206.06215 ; Montegriffo et al. 2023, A&A 674, A3 (external calibration; ±2% above 400 nm, colour-dependent systematics below) — https://arxiv.org/abs/2206.06205 ; Huang et al. 2024, ApJS — https://iopscience.iop.org/article/10.3847/1538-4365/ad18b1 ; GaiaXPy — https://www.cosmos.esa.int/web/gaia/gaiaxpy.
- Weiler, Jordi, Fabricius, Carrasco 2018, *Passband reconstruction from photometry* — https://arxiv.org/abs/1802.01667 ; Weiler 2018, A&A 617, A138 — https://arxiv.org/abs/1805.08082 ; Maíz Apellániz & Weiler 2018 — https://arxiv.org/abs/1808.02820 ; Bessell 2000, PASP 112, 961.
- Garrappa, Ofek et al. 2025, per-image transmission fitting against Gaia XP — https://arxiv.org/abs/2412.13257.
- Cardiel et al. 2021, MNRAS 507, 318 (standard RGB from the Jiang set) — https://arxiv.org/abs/2107.08734 ; Carrasco et al. 2023 — https://arxiv.org/abs/2303.14147.
- AAVSO DSLR Observing Manual v1.4 — https://www.aavso.org/sites/default/files/publications_files/dslr_manual/AAVSO_DSLR_Observing_Manual_V1-4.pdf.

**Sensor identity and the Z-body curves**
- TechInsights, *Sony IMX820 partially stacked image sensor* (extracted from a Nikon Z6 III) — https://www.techinsights.com/blog/sony-imx820-partially-stacked-image-sensor-device-essentials ; Sony Semiconductor product table (IMX820 "CoW BI" vs IMX410 "BI") — https://www.sony-semicon.com/en/products/is/camera/index.html ; Nikon press release 2024-06-17 — https://www.nikonusa.com/press-room/nikon-z6iii ; DPReview Z6 III specifications (Bayer) — https://www.dpreview.com/products/nikon/slrs/nikon_z6iii/specifications.
- Z6 II = Z6 sensor — https://en.wikipedia.org/wiki/Nikon_Z6II , https://www.dxomark.com/nikon-z6-ii-sensor-review-familiar-sensor-performance/ ; Z f "believed" — https://en.wikipedia.org/wiki/Nikon_Zf ; Z9 IMX609AQJ — https://en.wikipedia.org/wiki/Nikon_Z9 ; TechInsights IMX410 (Sony α7 III) — https://www.techinsights.com/products/def-1806-802 ; Nikon Rumors sensor table (secondary, self-described "not official") — https://nikonrumors.com/2025/09/28/who-produces-the-sensors-for-nikons-mirrorless-cameras.aspx/.
- Kolari Z6 teardown (0.3 mm dust glass + 0.8 mm UV/IR-cut) — https://kolarivision.com/nikon-z6-disassembly-teardown/ ; Z6 III teardown — https://kolarivision.com/nikon-z6iii-disassembly-and-teardown/ ; Kolari internal cut-filter transmissions (the SVO `_Block` source) — https://kolarivision.com/articles/internal-cut-filter-transmission/ ; Clarkvision on hot-mirror generations — https://clarkvision.com/articles/do_you_need_a_modified_camera_for_astrophotography/.
- ASWF `rawtoaces-data`, `data/camera/Nikon_Z_f_380_780_5.json` (Weta Digital "lightsaber", Apache-2.0, commit `cf6452c`) — https://github.com/AcademySoftwareFoundation/rawtoaces-data/tree/main/data/camera ; Weta physlight camera SSFs (Winquist & Thurston 2022) — https://zenodo.org/records/6590768 , https://github.com/wetadigital/physlight.
- Shelley, Nikon Z6 astro review (grating on a sunlit target) — https://markshelley.co.uk/Astronomy/nikonz6_review.html ; Delley, DPReview "Nikon Z color gamut" (blocked; snippet) — https://www.dpreview.com/forums/threads/nikon-z-color-gamut.4630168/page-2.
- SVO "Cameras/Nikon" relay pages (cite camspec and Kolari) — http://svo2.cab.inta-csic.es/theory/fps/index.php?mode=browse&gname=Cameras&gname2=Nikon ; camspec database page — https://www.gujinwei.org/research/camspec/db.html ; Zhao/Kawakami database — https://open-vision.sc.e.titech.ac.jp/~reikawa/research/cs/zhao/database.html ; Darrodi data — https://spectralestimation.wordpress.com/data/ ; maxmax D700 study (modified body) — https://maxmax.com/faq/camera-tech/spectral-response/nikon-d700-study ; beyondvisible — http://www.beyondvisible.com/bv2-dslrqe.html.
- siril-spcc-database commits `39aca582` ("Add Nikon cameras", direct commit) and `9f97c82a` (`is_dslr`) — https://gitlab.com/free-astro/siril-spcc-database/-/commit/39aca58226a4d0a04cd71c8a44498713fd7f2a88.

## 3. Verdict / recommendation

Adopt **Option 0 now** (runner fix; the null path becomes a loud error and
named curves are honoured — H0 measured both on the shipped july31/set-01
input; this retires a false statement in every record and is independent of
any curve), then **A1 — the Weta-measured Nikon Z f —
under the §4 test** with A1′ (Butcher Z6) and A2 (D750) as its control arms;
on a WIN, contribute the Z f conversion upstream (Apache-2.0 → GPLv3 is
one-way compatible; issue #3 asks for exactly this) and pin it in the
recipes' `spcc` block with its removal condition; **B1** is the
standards-grade endpoint, owner-gated on a grating and a night, and the only
path to a Z6 III entry. **C is out of bounds** as a calibration. The drafted
queue item is BACKLOG `spcc-sensor-curve`.

## 4. Pre-registered test — what decides "improvement" when a curve is tried

Runs after the campaign, on ONE product: the canonical per-set final of
**july31/set-01** as it stands then (its `_wcs.fit` is the input; SPCC is
re-run from it, nothing upstream is rebuilt). Six arms from the same
`_wcs.fit`, each a fresh `siril-cli` process (five full runs of ~2–3 min
on the 4920×3580 product and one that must fail fast):

- **A (control)** — today's runner, no spec. Must reproduce the shipped
  record for that product to the digit (SPCC measured deterministic on
  re-runs: the zero-point campaign's H1, `datasets/corpus/campaign_zeropoint/campaign_record.json`). Reference numbers on today's
  july31/set-01 `_full`: K 1.000/0.687/0.927, 3077/5119 stars, R/G
  `0.4887 + 0.2395·x` σ 0.140, B/G `0.2862 + 0.4620·x` σ 0.110, intercept
  share 0.71/0.39, "imprecise solution" fired.
- **A0** — Option 0 runner with NO spec: must **error** with Siril's own
  "not specified as argument or guessable from previous use" line and write
  no product.
- **B** — Option 0 runner, `"-oscsensor=Nikon Z f"` (A1, converted to a
  photon-based curve: divided by λ, renormalised — §1.6),
  `"-oscfilter=No filter"`, `"-whiteref=Average Spiral Galaxy"` — every
  argument whole-token quoted, the form Siril's `help spcc` documents and H0
  exercised.
- **B′** — same, `"-oscsensor=Nikon Z6"` (A1′, same conversion).
- **B″** — same, `"-oscsensor=Nikon D750"` (A2, as the database ships it).
  H0 already ran this arm once without `save` (K 1.000/0.697/0.945, R/G
  `0.3265 + 0.6247·x` σ 0.095, B/G `0.3112 + 0.6040·x` σ 0.107, 3077/5119): the
  six-arm run must reproduce it to the digit, the determinism check.
- **B°** (convention probe, one extra run) — the Z f curve as shipped
  (energy-based, no `/λ`): measures how much the QE-vs-responsivity
  convention moves K and the fit; expected small by §1.1(ii); it decides
  which convention the upstream MR states, not which "fits better".

Measures — every one is Siril's own log line or a Siril `stat`, captured by
the existing runner and `regional_stat.py`:

- **H0 — resolution positive control (STOP if it fails):** in B/B′/B″ the
  log's `SPCC JSON metadata loaded` precedes `SPCC will use OSC sensor
  "<name>"…`; K differs between at least two of B/B′/B″ in at least one
  channel by > 0.002 (the printed precision); A0 errors. If all three arms
  print one K, the names were not honoured and nothing else in this test
  means anything.
- **H1 — model adequacy (the grade):** on B, the intercept share falls from
  0.71 (R/G) and 0.39 (B/G) to **≤ 0.25 and ≤ 0.15** [WIN]; unchanged within
  ±0.05 on ALL of B/B′/B″ [NULL — the intercept is not curve-driven; suspect
  the photometry in a dense 17″/px field]; the arms differ but none meets
  the bar [needs the B1 measurement, not more proxies]. Secondary: fit σ on
  both colours < 0.10 so the "imprecise solution" line stops firing [WIN on
  its own]; `n_kept` within ±5% of A (photometry does not see the curve — a
  larger move means the input differed).
- **H2 — K delta, declared:** ΔK_G, ΔK_B for each arm vs A, reported as
  numbers; expected |ΔK| ≲ 5% from §1.1(ii); > 10% on B is a flag to
  re-check the white reference resolved (its catalogue colour under the new
  curve is recoverable from the log as in §1.2 and must be one value across
  arms of the same curve).
- **H3 — band vs outer sky:** `regional_stat.py` boxes at the band and at
  the outer sky, same pixel boxes on the A and B linear `_spcc` products;
  predicted band shift = ΔK_R/ΔK_G and ΔK_B/ΔK_G exactly; a measured shift
  that departs from the prediction by > 0.005 in either ratio means something
  other than K moved (an offset, or a box mismatch). Whether the resulting
  band colour is RIGHT is not a question the data settles.
- **H4 — the owner's eyes:** `web/results/july31/judge/set-01_<tag>_spcc-linked.png`
  for B beside A, 16-bit, same canvas, same stretch rule (per-product
  `autostretch -linked` — independent products), no crops. Aesthetic; the
  only verdict on colour.

Verdict form: WIN / NULL / needs-eyes per the bars; a NULL on H1 for all
three curves is the finding that the fit geometry is not curve-driven and
closes A1/A1′/A2 without a B1 capture being implied. Cost: five SPCC runs, one
fast failure, two finishes; no from-raws, no compose.

## 5. UNCHECKED — premises this work rests on and did not test

- **That the preload is WHAT makes names resolve** — H0 measured that
  `spcc_list` + a name resolves and that no name errors; it did not run a
  named arm WITHOUT `spcc_list`, so "a bare `-oscsensor=` silently uses index
  0" rests on the source order plus the 48 shipped logs' order, not on a
  measurement. One more one-minute arm settles it.
- **The `-oscsensor="Nikon D750"` quoting form** (value-only quotes) is
  neither Siril's documented form nor exercised — only the whole-token form
  was; the runner uses the whole-token form.
- **"Nothing written" in H0** was checked by the input's bytes/mtime and
  `git status` only; Siril's own cache directories were not inventoried. The
  3077 kept stars are equal in count to the shipped run's, not verified as
  the same set.
- **The binary is tag 1.4.4** — assumed from the flatpak's version string and
  matching message strings.
- **Sensor lineage** — Z6 III = IMX820AQJ is a teardown (TechInsights); Z6 =
  IMX410 has no teardown (consensus only); Z f = Z6 II sensor is "believed"
  (Wikipedia); **Z6 III CFA dyes and hot mirror = Z f's / Z6's is assumed by
  everyone and measured by no one.**
- **The Weta "lightsaber" method** is undocumented and its "relative" units
  undefined (QE vs responsivity); B° measures the convention's effect, it
  does not settle which is right — physics does (§1.6), and the §4 arms apply
  one stated convention.
- **Butcher's Z6 curve provenance** — lamp power calibration unstated;
  two-decimal values; grating efficiency handling unstated.
- **The D750 entry's convention** — used as the database ships it.
- **The director's band numbers** (0.989 / 0.960 / ~1.00) — untracked;
  re-measured only by H3.
- **That the green excess is attributable to K at all** — §1.8 names two
  alternatives with discriminators; this item does not run them.
- **That the "imprecise solution" σ is model-driven rather than
  photometry-driven** — the reason H1 has a NULL branch and three curves.
- **Shared with the director and REFUTED here rather than confirmed:** "the
  sensor-null default applies siril's generic response" (no such path exists);
  "K factors ride a generic curve" (they rode Generic-mono × Antlia RGB);
  "contributing the curve to the database is the fix" (necessary, not
  sufficient — without Option 0 a contributed curve is not what runs);
  "the local database's Nikon coverage is the D200" (it is 13 D-bodies — the
  gap is the Z line, not Nikon).
- **Shared premise not tested by either session:** that SPCC (three scalars
  + three offsets against Gaia XP through a response model, one airmass, one
  white reference) is the right instrument for a 28.6° field — the industry
  position (§1.6), not a measurement on this class.

## 6. Status

**PROVISIONAL, with H0 RUN AND PASSED** (`spcc_h0_probe.json`: the preload
resolves names, two names give two K, the null spec errors, nothing written).
The resolution mechanism is MEASURED through the 48 shipped logs and the
probe; the curve test (§4 H1–H4) has not run; stage 0's runner fix is in
progress. Nothing here changes a product.

## 7. Graduation

None yet. When §4 runs: the headless resolution trap and the index-0 model
earn a `docs/dead-ends/siril-behaviors.md` entry (it changes a decision:
every future SPCC invocation, and every reading of an old K record); the
false "generic default" wording is swept from the seven sites in §1.7;
`TOOLS.md`'s SPCC row gains the `spcc_list`-first rule and the `is_dslr`/LPF
requirement; the item's removal-condition rows go into BACKLOG's register.
