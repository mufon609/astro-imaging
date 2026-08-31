# Stacking chain vs official pipelines (Siril doctrine + WBPP reference) — deep dive

- **Question / scope** — How far does the repo's chain (calibrate → [undistort]
  → register → stack → **combine**) diverge from what the tool vendors
  themselves prescribe: Siril's own official doctrine (docs + FAQ + the scripts
  that ship with the app + team statements) and PixInsight WBPP as the industry
  reference — audited stage-by-stage. This is the standing re-verification
  README's reference-standard table requires, run as its own investigation.
- **Version anchors, last checked 2026-08-31 against primary sources — all four
  UNCHANGED since the previous check.** Siril **1.4.4** stable (2026-06-17;
  siril.org/download/ lists nothing newer, and 1.5.0 is dev-only —
  readthedocs `/en/latest` builds as "Siril 1.5.0 documentation"); PixInsight
  **1.9.4 Lockhart build 1695** (2026-06-21) + **WBPP 2.9.0** (2026-01-14,
  pixinsight.net/dev); DSS **6.2.2** (2026-07-18); APP **2.0.0-beta46**. The
  rig runs Siril 1.4.4 (`flatpak list`), so doctrine and binary agree.
- **Rig** — x86-64 Kali, 28 threads, 31 GB, no GPU, flatpak Siril, headless
  throughout.
- **THE §D DATA IS ARCHIVED, NOT LOST — the measurements stand.** §D was run on
  july23 (Nikon Z6III + 24-70/4 S @ 70 mm, 4 sets × ~400 × 3 s ISO 1600, fixed
  tripod — declared and solve-confirmed, RA advancing at the sidereal rate, Dec
  constant to 0.03°/set — flatless by acquisition, 211 matched darks). That
  session was later reset to raws (`scripts/session_archive.sh`) and is not
  under `sessions/`. Its RECORDS are: `3554aa3` is an ancestor of HEAD and
  carries all four sets — `git show 3554aa3:datasets/july23/` — including every
  path §D cites (verified per-path with `git cat-file -e`). Citing a COMMIT
  rather than a working-tree path is this repo's standing convention, and the
  reason is live here: a bare path into a reset session goes dangling, which is
  what `check_doc_pointers` caught in the first draft of this very note. A wiped
  dataset does not retract a measurement — what a §D number can no longer do is
  be RE-measured in place, so each is a fixed historical reading of a chain
  revision, not a live one.
  Every doctrine claim below carries its source; repo-side numbers cite the
  tracked records.

## Findings

### A. The official Siril 1.4.4 chain (primary sources)

**TWO GITLAB REPOS, TWO EVIDENCE CLASSES — do not cite them alike.**
`gitlab.com/free-astro/siril` `scripts/` is what SHIPS WITH THE APP: at tag
1.4.4 exactly six files — `Mono_Preprocessing.ssf`, `OSC_Extract_Ha.ssf`,
`OSC_Extract_HaOIII.ssf`, `OSC_Preprocessing.ssf`,
`OSC_Preprocessing_BayerDrizzle.ssf`, `RGB_Composition.ssf` (listed via the
GitLab tree API at `ref=1.4.4`). `gitlab.com/free-astro/siril-scripts` is, by
its own README, the **"External Script Repository … contributed by users"** —
curated in the vendor's namespace, but COMMUNITY evidence, not vendor doctrine.
Everything below is labelled by which one it comes from.

Current stable: 1.4.4 (2026-06-17). The canonical `OSC_Preprocessing.ssf`
(SHIPPED, `free-astro/siril` @1.4.4; header "Preprocessing v1.4",
`requires 1.3.4`) runs exactly — fetched verbatim, `convert`/`cd` elided:

```
stack bias rej 3 3 -nonorm -out=../masters/bias_stacked
calibrate flat -bias=../masters/bias_stacked
stack pp_flat rej 3 3 -norm=mul -out=../masters/pp_flat_stacked
stack dark rej 3 3 -nonorm -out=../masters/dark_stacked
calibrate light -dark=../masters/dark_stacked -flat=../masters/pp_flat_stacked
          -cc=dark -cfa -equalize_cfa -debayer
register pp_light                       # one pass, homography, lanczos4+clamp
stack r_pp_light rej 3 3 -norm=addscale -output_norm -rgb_equal -32b -out=result
load result                             # ← the three commands a previous
mirrorx -bottomup                       #   revision of this block dropped:
save ../result_$LIVETIME:%d$s           #   the script does not end at `stack`
```

No plate solve, no SPCC, no quality culls in the official script — the pixel
chain ends at the linear 32-bit stack, followed by an orientation flip and a
save. **`OSC_Preprocessing_BayerDrizzle.ssf` SHIPS ALONGSIDE IT** (same repo,
same tag), which makes Bayer drizzle a vendor-shipped ROUTE rather than only a
recommendation on the SPCC page: its calibrate drops `-debayer` (CFA must stay
mosaiced) and its registration line is
`register pp_light -drizzle -scale=1.0 -pixfrac=1.0 -kernel=square
-flat=../masters/pp_flat_stacked`; the stack line is identical to the
non-drizzle script's. Doctrine highlights (docs =
siril.readthedocs.io/en/stable, i.e. the 1.4.4 build; FAQ = siril.org/faq):

- **Calibration formula is (L − D)/(F − O)**: bias calibrates the FLAT only;
  lights get matched dark + flat (the dark carries the bias). Darks: same
  exposure/ISO, "approximately the same temperature ... this is the reason we
  make dark frames at the end, or in the middle of the imaging session"
  (calibration.html). FAQ adds: for non-cooled cameras over long sessions "the
  correct way ... is to use dark optimisation" (`-opt`, bias-calibrated darks).
- **No flats shot → the answer on offer is to SKIP flat division entirely**, and
  the evidence for that is an ARTIFACT, not a statement.
  `OSC_Preprocessing_WithoutFlat.ssf` (COMMUNITY, `siril-scripts`) calibrates
  `calibrate light -dark=dark_stacked -cfa -equalize_cfa -debayer` — no
  `-flat=`, and no `-cc=` either — then registers and stacks as usual.
  **The FAQ does NOT prescribe this**, and an earlier revision of this bullet
  cited it as if it did: FAQ "I don't have flats, how can I use scripts?" says
  only that the official scripts assume dark+flat+flat-dark and *"you will have
  to either modify the script … or find one that has already fits your needs in
  the dedicated page"*. The redirect is the doctrine; the script is the
  instance. No official source endorses or rejects building a flat from the
  lights themselves (absence of doctrine, searched docs/FAQ/blog/forums).
- **Cosmetic correction**: script uses bare `-cc=dark` = hot-only σ3;
  `-cc=dark 3 3` (docs) adds cold-pixel correction.
- **Registration**: homography is default and "strongly recommended for
  wide-field images"; `-2pass` is the docs' own better-reference improvement
  (compute transforms first, then `seqapplyreg`); lanczos4 + clamping default.
  **Lens distortion is now handled natively**: platesolve fits SIP (default
  Cubic, to order 5 — "Unless you have a perfectly optically flat field, it is
  usualy a good idea to platesolve using SIP") and `register -disto=image|
  file|master` applies it, correcting star positions before the fit and
  composing undistort+projection into ONE resampling at export
  (registration.html; the DSA script in the official repo is the worked
  example). 1.4 also drives local astrometry.net blind solves natively
  (`platesolve -localasnet -blindpos -blindres`).
- **Stacking**: rejection by sub count — percentile "ideal for small sets (up
  to 6 images)"; GESD "excellent performances with large dataset of more 50
  images" (parameters are outlier FRACTION + SIGNIFICANCE — Siril's own GUI
  defaults 0.3/0.05, from `src/gui/stacking.c`); winsorized 3/3 is the factory
  default between; linear-fit for "large stacks and images containing sky
  gradients with differing spatial distributions". Lights normalize
  additive+scaling (default), `-output_norm` rescales the result; flats
  `-norm=mul`; masters `-nonorm`. `-rgb_equal` is conditioned by the command
  reference on SPCC/PCC NOT being used later (`help stack`, verbatim: *"useful
  if PCC/SPCC or unlinked AUTOSTRETCH will not be used"*). Weighting: factory
  `NO_WEIGHT`, no official script uses `-weight=`, docs prescribe nothing.
- **MULTI-NIGHT — Siril states a doctrine here and this audit did not carry it
  until now.** FAQ "How do I process several sessions?", verbatim: *"The correct
  way to go is: Calibrate all sessions independently with the corresponding
  master files. Register all preprocessed images together."* — per-session
  calibration, then **ONE registration and ONE integration over every frame of
  every night**, assembled by giving each session a disjoint conversion index
  so the files form a single sequence. The community
  `osc-multi-night-stacking-v1.2.py` (`siril-scripts`) implements exactly that
  shape: per-session masters → `merge "<sess1>/pp_light" "<sess2>/pp_light" …
  all_sessions` → `register all_sessions` → one `stack r_all_sessions`. It is
  the ONE stage where the vendor prescribes a chain shape this repo does not
  build (row in §B). Note the vendor also draws a boundary: mixed EXPOSURES are
  explicitly *not* to be integrated together (FAQ, "combine different
  exposures" — stack each separately, blend as layers).
- **Stack options present in 1.4.4 that this audit has never covered** —
  MEASURED on the rig's own binary, `help stack` / `help seqapplyreg` under
  siril 1.4.4, not read from a doc: `-overlap_norm` (*"compute normalization
  coefficients on images overlaps instead of whole images (allowed only if
  `-maximize` is passed)"*), `-feather=<px>` (feathering mask on each image's
  borders), `-maximize` (stack the union — *"`-framing=max` … The resulting
  sequence can then be stacked using option `-maximize` of STACK"*, so the two
  are a documented PAIR), `-upscale`, `-rejmap[s]`, and two rejection
  algorithms beyond the three this repo's ladder selects: **linear-fit** (`l`)
  and **k-MAD** (`a`). The stacking doc's own indication for linear-fit is
  *"performs very well with large stacks and images containing sky gradients
  with differing spatial distributions"*.
- **Bit depth**: 32-bit default; "a 16-bit stacking can lose a lot of
  information" (preferences_gui.html); official scripts pin `-32b`.
- **Quality filtering**: official scripts cull nothing; FAQ offers
  `-filter-fwhm=75%` only as an optional user tweak.
- **Color**: SPCC mandatory on the linear, plate-solved stack; official
  post-stack order: crop → background extraction → photometric colour →
  deconv → stretch → SCNR → saturation → export. For OSC colour the SPCC page
  recommends the Bayer-drizzle variant ("Drizzle provides a significant
  improvement over debayering").

### B. Stage-by-stage: our chain vs Siril doctrine

Our chain = the wide-field-untracked route: `run_undistort_pipeline.sh` (and
its standing groups driver `run_undistort_groups.sh`) with per-set sky flats
(`build_sky_flat.sh`), composed by `run_undistort_compose.sh` /
`run_corpus_combine.sh`. Rows are read from the builders as shipped, not from a
past run. **The tracked-mount STANDARD route (`run_pipeline.sh` +
`scripts/stack/siril/lights.ssf.tmpl`) is a SEPARATE chain and diverges from
this table in one row (normalization) — it is called out there rather than
averaged in, and it has no dataset on the tree to measure on
(BACKLOG:`standard-route-output-norm`).**

| stage | official Siril doctrine | our chain | verdict |
|---|---|---|---|
| master dark | `stack dark rej 3 3 -nonorm`, matched exp/ISO, same-session temperature | identical, 211 matched darks shot immediately after the last light (02:33), 2 exposure-strays excluded by EXIF match | **MATCH** |
| bias | on flats only; lights never (dark carries it) | no bias anywhere; sky-flat inputs are dark-subtracted (offset leaves via the dark), flat denominator therefore pedestal-free | **MATCH in intent** — mechanism differs, recorded |
| dark optimization | skip for matched darks; FAQ recommends `-opt` for uncooled cameras | not used — darks are same-night, shot at session-end temperature | **MATCH (base doctrine)**; FAQ fork noted → named test below |
| flat | real flats; if none shot, official answer = no flat at all | per-set sky flat from the set's own lights (mul-norm, winsorized), validation-gated (regional falloff, 0 specks, preview eye check) | **DIVERGENCE (documented adaptation)** — official alternative leaves ~2× corner falloff uncorrected with no native multiplicative fixer (`subsky` is subtraction-only); no official position exists on light-built flats; removal condition = a real matching flat |
| light calibrate | `-dark -cc=dark -cfa -equalize_cfa -debayer` | `-dark -cc=dark 3 3 -flat=<skyflat> -equalize_cfa -cfa -debayer` | **MATCH+** (adds documented cold-pixel side; `-cc=dark` is mandatory repo-wide — walking-noise lesson) |
| debayer timing | calibrate CFA, debayer after | identical | **MATCH** (Bayer-drizzle colour variant noted below) |
| undistort | native: SIP platesolve + `register -disto=` | darktable + lensfun model FITTED from the set's own frames, warped before registration | **DIVERGENCE (measured adaptation)** — astrometry.net per-frame SIP at this field scale is a measured LOSS (majFWHM 4.74→6.02 px, dead-ends registry); Siril-native SIP from its own solver is UNTESTED on this class and is the fitted model's written removal condition → named test below |
| register | homography; `-2pass` documented improvement; official script 1-pass | `register -2pass` + `seqapplyreg -framing=min` | **MATCH (docs-side)**; `-framing=min` is documented, neutral; 2-pass beats script default per docs' own rationale |
| rejection | ≤6 percentile; >50 GESD 0.3/0.05 (tool defaults); winsorized 3/3 factory default between | `stack_rejection.sh`: percentile ≤6, winsorized 7–50, GESD >50 at 0.3/0.05 | **MATCH** (the 7–50 winsorized band is our inference; docs state no band) |
| normalization | lights addscale + `-output_norm` | `-norm=addscale` and **NO `-output_norm`** on the undistort route (`run_undistort_pipeline.sh`:89/332-342, `run_undistort_groups.sh`:364-378, `run_undistort_compose.sh`:377-388); the reference's IKSS location/scale is stamped as `ANCLOC*`/`ANCSCL*`/`ANCREF` instead | **DIVERGENCE (measured adaptation)** — `-output_norm` is a global min-max rescale to [0,1] (`help stack`, verbatim), i.e. one zero-point keyed to whichever member held the extremum, which breaks cross-night level comparability; mechanism + shipped design in `docs/dead-ends/stacking-compose.md`, the `-output_norm` zero-point entry. Removal condition: Siril offering a reference-anchored (non-min-max) output normalization. **A previous revision of this row read "identical / MATCH", which was false for the chain this table names** |
| normalization (STANDARD route only) | as above | `run_pipeline.sh`:331/333/348 + `lights.ssf.tmpl`:37 still pass `-norm=addscale -output_norm` | **MATCH with the vendor, and an INTERNAL split** — the closure above was never applied here because no tracked-mount dataset exists to declare a delta on; watchlist-gated, BACKLOG:`standard-route-output-norm` |
| rejection ALGORITHM coverage | six algorithms offered; docs indicate linear-fit for *"large stacks and images containing sky gradients with differing spatial distributions"* | `stack_rejection.sh` selects among three (percentile / winsorized / GESD) by sub count; **linear-fit and k-MAD are never selected** | **UNEXAMINED** — not a justified deviation and not drift-with-a-reason: `k-MAD` and `rej a ` together match 0 of 1042 tracked text files (same denominator as the row below), and linear-fit appears once in `TOOLS.md` as an option with no branch and no recorded reason for not taking it. The doc's own indication describes an untracked drifting set → named test E1 |
| `-rgb_equal` | script passes it; command doc conditions it on NOT using SPCC | omitted (we run SPCC) | **MATCH (doc-side)** — the official script and its own command doc disagree; we follow the doc condition |
| weighting | factory NO_WEIGHT; nothing prescribed | off, per-set recipe records why (measured min-max-ramp soft-cull at low spread) | **MATCH** |
| culling | official scripts none; `-filter-*` optional | recorded per-frame QA policy → recipe exclude with reasons (session-edge settle, frame-wide degradation, aircraft; satellites kept) | **EXTENSION** — no conflict; official filters cull on registration metrics only, blind to transient classes |
| bit depth | 32-bit; docs warn 16-bit stacking loses information | 32-bit float END TO END and PINNED: `set32bits` in `lights.ssf.tmpl`:10 and in every `.ssf` `run_undistort_pipeline.sh` emits | **MATCH+ — the divergence is RETIRED and now GUARDED.** `check_bitdepth.sh` (rostered in `run_guards.sh`) fails the tree if any script pins `set16bits` outside four named diagnostic exemptions, and requires every product builder to EMIT `set32bits` + `setcompress 0`. Remaining `set16bits` hits are diagnostics under `datasets/aug06/corner_work/` + `datasets/aug06/set-01/drift_work/`, off every build path. **The row previously read as an open divergence with a fired-but-unapplied condition; it is applied.** Retirement cost, measured: 16-bit round-tripping kept only ~55-70% of the 32-bit arm's extended faint contrast (NAN-region 4.8/2.4/3.9 vs 8.5/2.9/5.6 % of local sky, R/G/B), and a 16-bit master dark inflates the fixed-pattern residual 0.4213 → 0.5109 ADU (+21%) |
| solve | native `platesolve` incl. `-localasnet` blind | external astrometry.net xylist route (sep extractor) — Siril's findstar-based matcher measured failing ultra-wide TRAILED fields | **DIVERGENCE (measured adaptation)** — the july23 class is only mildly trailed (roundness 0.80 vs july14's 0.615), so the native solver deserves a re-probe on this class → named test below |
| SPCC | linear + solved, before stretch; after crop/BGE in the official order | SPCC directly on the raw solved stack (BGE is a render-tier gap; K-delta order-robustness check pre-registered in README) | **MATCH with recorded gap** |
| **multi-night combine** | **FAQ: calibrate each session independently, then REGISTER AND INTEGRATE EVERY FRAME OF EVERY NIGHT AS ONE SEQUENCE** (community `osc-multi-night-stacking-v1.2.py` does it as `merge … all_sessions` → one `register` → one `stack`) | per-set/per-group SUB-STACKS, composed astrometrically: `run_undistort_compose.sh` links the members, `seqapplyreg -framing=min\|max`, then `stack r_s mean none -norm=addscale -weight=nbstack` — plain mean, **no rejection at the compose** | **DIVERGENCE — mechanism measured and recorded, but never before stated AS a deviation from a named vendor prescription.** The mechanism that forbids the vendor shape here: one global homography cannot register a far-drifting wide set (`docs/wide-field-untracked-registration.md` — the whole reason the undistort class exists), and a distortion model describes ONE optical state, so a single sequence spanning nights has no single correct warp — **4.07 px** cross-night disagreement on the same star under a shared model (`docs/combine-contract.md` §0.2, which carries that figure and only that figure), measured against the **0.14 / 0.19 px** same-set/same-model/same-state floor, which lives in `run_undistort_compose.sh`'s own member-separation ladder — a different artifact, cited separately on purpose. Both facts are on this rig. What was missing is the standards-first half: the vendor's route named, then the measured reason for leaving it |
| compose framing + union normalization | `-framing=max` is documented to pair with `stack -maximize`, which can then take `-overlap_norm` (normalization coefficients on the OVERLAPS) and `-feather=` | `seqapplyreg s -framing=max` then `stack r_s mean none -norm=addscale` — **none of the three appears anywhere in the repo as a flag: `-maximize`, `-overlap_norm` and `-feather=` each match 0 of 1042 tracked text files** (`git ls-files` over `*.md *.sh *.py *.tmpl *.ssf *.json *.jsonl`, this doc and `TOOLS.md` excluded) | **UNRECORDED DEVIATION.** The repo's own aug06 audit already reached this conclusion and it lives only in a ledger: *"Mainstream-documented consequence of composing members with unmatched background gradients (Siril mosaics tutorial per-frame degree-1 + overlap_norm/feather; PI LN/NSG/adaptive; APP LNC/MBB; SWarp SUBTRACT_BACK default) — the route omits the step every surveyed pipeline inserts"* (`datasets/aug06/experiments.jsonl`, `combine_corner_fail_investigation`). Its follow-up records compose-side FEATHERING as NOT a candidate for that defect class (it blends the step rather than removing it) — but `-overlap_norm` is a DIFFERENT mechanism and no entry rules on it. Whether the pairing costs anything here is UNMEASURED → named test E2 |

### C. PixInsight WBPP / industry reference

Version anchor (last checked 2026-08-31, all unchanged): PixInsight **1.9.4
Lockhart build 1695** (2026-06-21), **WBPP 2.9.0** (2026-01-14); DSS 6.2.2
(2026-07-18, now cross-platform); APP 2.0.0-beta46. WBPP stage order:
calibrate (auto pedestal) → auto
CosmeticCorrection from the master dark (default-on since 2.7.5) → debayer →
measurement (PSF metadata) → opt-in Frame Selection (new in 2.9.0) →
StarAlignment → LocalNormalization → ImageIntegration → Autocrop →
astrometric solution on masters.

Where WBPP doctrine and Siril doctrine (and ours) stand against each other:

| axis | PixInsight/WBPP doctrine | Siril doctrine / our chain |
|---|---|---|
| master dark | average, no normalization, winsorized, no bias, no optimization for matched darks ("bias not required ... already present in dark frames"; optimization fails on amp glow) | **identical** — full agreement across all three |
| cosmetic correction | auto-CC from the master dark, default-on | `-cc=dark` from the dark's bad-pixel map — **same mechanism**, ours mandatory repo-wide |
| flats when none shot | no sanctioned lights-built flat; gradient tools are ADDITIVE-only by their own docs (GradientCorrection "purely additive"; MARS leaves multiplicative to Gaia normalization). APP alone sanctions an analytic vignetting model (Kang-Weiss artificial flats) | our per-set sky flat has no vendor precedent anywhere; closest official relative is Peris's twilight sky-flat procedure (percentile clip <0.02 to kill stars) — winsorized on ~400 drifting lights is our own validated mechanism |
| weighting | PSF Signal Weight default-on; bad frames get weight≈0, not exclusion ("no more a real need of throwing away frames" — Sartori); min-weight 0.005 is a compute-saver, not a cull | Siril factory NO_WEIGHT, no script weights; ours off with the measured min-max-ramp pathology. **Genuine philosophical split** — PI's normalized photometric weights have no ramp pathology; Siril has no PSFSW equivalent (standing TOOLS.md gap, still true at 2.9.0) |
| local normalization | between registration and integration, "crucial" with time-varying gradients, default-enabled | **still a genuine gap, but "global addscale only" was imprecise and is corrected here.** Siril 1.4.4 ships `-overlap_norm` and `-feather=` (MEASURED on this rig's binary, `help stack`). Neither closes it: `-overlap_norm` changes only WHERE the coefficients are ESTIMATED (the images' overlaps instead of the whole frame) and still yields one location+scale pair per image, i.e. a global affine normalization; PI's LocalNormalization fits a spatially-VARYING model. `-feather` is a border blend, not a normalization at all. The gap is in the model's degrees of freedom, and it is open |
| registration | homography default + thin-plate-spline distortion correction for wide fields/mosaics; **external distortion models** "pre-correct the images for optical aberrations ... so the registration process can work with undistorted alignment references" | Siril: homography only (+SIP `-disto=` since 1.4). Our darktable pre-warp is mechanically the PI *external distortion model* idea, executed out-of-band — the need is recognized by every vendor (APP: enable distortion correction when RMS >0.5 px; DSS: polynomial warp) |
| rejection by N | WBPP Auto: <6 percentile, 6–15 winsorized, **≥15 GESD**; "we consider ESD the best rejection algorithm currently available" (Conejero); sigma defaults asymmetric 4/2 | Siril: ≤6 percentile, >50 GESD, winsorized between (3/3 convention). Ours follows Siril; both vendors converge on percentile-small / winsorized-mid / GESD-deep — they differ only on where GESD starts (15 vs 50) |
| lights normalization | additive-with-scaling + scaled output — Table 1 | **identical** |
| framing | register to reference geometry, **Autocrop the master after** integration | ours crops BEFORE (`-framing=min`) — same intent, opposite order |
| OSC colour | CFA (Bayer) drizzle is THE recommended final path; demosaiced integration = "temporary working images" | Siril's standard script (and ours) demosaics at calibrate; Siril's own SPCC page now also recommends Bayer drizzle — **the sharpest doctrinal split**, and for our class it is chained on moving undistortion inside Siril (drizzle needs CFA in; the darktable warp needs demosaiced in) |
| culling | keep-and-weight; 2.9.0 adds opt-in metric-threshold Frame Selection (preview aimed at "satellites, aircraft trails") | our recorded-QA-policy cull (~0–2 frames/set) is the manual equivalent of that opt-in step |
| bit depth | float32 end-to-end, no 16-bit blessing anywhere | Siril: 32-bit default, 16-bit allowed with a warning; **ours is now float32 end-to-end and guarded, so all three vendors and this repo agree** — the `set16bits` divergence is retired, not merely condition-fired (§B) |
| multi-night | grouping keywords split the sessions so **calibration runs per session while registration and integration run over all sessions' frames together** — same shape as Siril's FAQ. EVIDENCE CLASS: community consensus (Cloudy Nights 769960 / 843093, pixinsight.com/forum 19589, star-watcher.ch), not a vendor doc sentence; the WBPP announcement pages are 403 to this rig's fetcher and were not read | ours composes per-set sub-stacks instead — **and the capability PI relies on to make that shape hold across nights is precisely the one Siril lacks**. The two rows are one finding seen twice: with only a global per-image normalization, a single cross-night integration has nothing to reconcile the nights' spatially-differing gradients with |

DSS cross-check: kappa-sigma/median-kappa-sigma defaults, median masters,
score-based reference, polynomial (not TPS) warp, hot pixels from the master
dark at median+16σ — an older, simpler doctrine that contradicts nothing
above. APP: quality weights (star count + SNR, offset by FWHM), LNC local
normalization, MBB blending, distortion correction on demand, "no outlier
rejection unless needed — the Bad Pixel Map takes care of hot/bad pixels".

### D. Measured on the july23 run — ARCHIVED EVIDENCE, not a live test

These are fixed historical readings of the chain revision that produced them.
The session was reset to raws and the products are gone; the RECORDS are at
`3554aa3` (an ancestor of HEAD, all four sets present), so every citation below
resolves and every number stands as measured. None of it can be re-measured in
place, so nothing here should be read as describing the chain as it ships today
— for that, read §B, which is taken from the builders.

- Frame QA (Siril `register -2pass` regdata, 1601 frames): 100% registration,
  zero match failures, per-set medians FWHM 2.633/2.648/2.675/2.718 px
  (CFA-sampled), roundness 0.798–0.803, background stable to 0.1%
  (`datasets/july23/set-0<N>/qa_work/frame_metrics.json`, archived — `git show 3554aa3:datasets/july23/`). The 3 s subs halve
  july14's in-exposure trail exactly as the acquisition checklist predicts
  (roundness 0.80 vs 0.615 at 6 s).
- Anomaly audit: satellites only in sets 01–02 (5 + 1 objects), no aircraft so
  far; culls are session-edge settle frames only (2/401, 0/400, 1/401 …).
- Fixed-mount fingerprint: set-01 sweeps RA 306.56°→313.44° in 27.2 min
  (15.18°/hr RA ≈ sidereal), Dec constant 43.69→43.66; the camera was re-aimed
  ~6.2° back between sets (set-02 starts at RA 307.25°) — four nearly
  coincident footprints (`datasets/july23/set-0<N>/fingerprint.json`, archived — `git show 3554aa3:datasets/july23/`; all four
  verdicts CONFIRM fixed).
- Stacks (single-pass undistort chain, ~2 h/set wall-clock serial): 399/400/
  400/398 of eligible frames registered AND stacked — zero registration loss
  across 1597 frames. GESD (0.3/0.05) per-channel rejection 0.001–0.5% —
  outlier tails only, exactly the doctrine intent at this depth. Stack
  background noise (Siril bgnoise, ADU): set-01 1.45/1.78/1.34 → set-04
  1.20/1.36/1.15 (R/G/B) — monotonic improvement matching the sky darkening
  QA saw (bg16 1065→1057).
- Blind solves on all four stacks + combine: 17.05–17.07″/px, centers RA
  309.6–310.8, Dec +41.9…+43.8 (the ~1.8° southward re-aim walk across the
  night); logodds 157–414.
- SPCC (spec-less run = the accidental index-0 model, "Generic mono sensor" ×
  Antlia R/G/B — `docs/spcc-sensor-curve-z6iii.md` §1.2; local Gaia XP): K factors R 1.000 across
  the board, G 0.686–0.728, B 0.883–0.967, ~2900–3120 of ~5100–5510
  photometry stars kept per product — one tight family, and the same ballpark
  as july14 set-01's tracked record (G 0.708, B 0.945): same sensor, sane.
- Combine (4-member min-framing compose of the per-set stacks, plain mean +
  nbstack weights, STACKCNT 1597): 4109×2612 full-depth canvas — the 4-way
  intersection after per-set drift crops (~1050 px each) and the re-aim
  scatter; NAN + Pelican + the Cygnus dark lanes comfortably inside.
  Union/groups framing stays available if the wider drift corridor is wanted.
- Judge surfaces (diagnostic linked autostretch, 16-bit PNG): clean at
  inspection scale — no seams, holes, rim artifacts, chroma blotches, or
  visible walking-noise streaks; uniform airglow tint expected (background
  extraction is the user-gated render tier, not this chain).
- One infrastructure lesson, measured: two concurrent rapid-fire flatpak
  siril-cli loops die probabilistically in bwrap sandbox setup (instance-dir
  cleanup race) — closed by the flock-serialized invoker
  (`scripts/lib/siril_run.sh`, removal-register row); the chain reran
  serialized and clean.
- **32-bit doctrine, vindicated on data:** 16-bit integer intermediates
  (1) quantized one channel's histogram to MAD=0, degenerating Siril's
  linked-autostretch statistics, and (2) suppressed extended-structure
  contrast ~30–45% (probe twin: NAN contrast 4.8/2.4/3.9 vs 8.5/2.9/5.6
  %-of-sky). The 32-bit chain reads contrast 15–37% of sky (SNR 6–13) vs
  ~10% (2.3–3.3) at full depth. Both vendors' float doctrine is measured
  signal protection on low-e-flux wide-field data, not conservatism.
- **The warp leg's ICC contract is level-critical:** the sRGB-tag-matched
  round trip carries a TRC toe mismatch below linear ≈0.003 (+4.7% at
  0.0015) that injected a radial corner chroma on 3 s-class data while
  leaving 6 s-class untouched; the fixed contract (untagged float TIFF +
  LIN_REC709 export) measures identity 1.0000 at every level. Registry ICC
  entry (mechanism + numbers).

### E. Doctrine deltas → named tests (pre-registered, not run here)

Each is a PROPOSAL for the owner with a stated method, not scheduled work.

1. **Linear-fit rejection vs GESD on a drifting untracked set** — Siril's own
   indication for `rej l` names this data ("large stacks and images containing
   sky gradients with differing spatial distributions"), and the repo has never
   evaluated it. One knob: `stack_rejection_for`'s >50 branch, `rej g 0.3 0.05`
   → `rej l 3 3`, on ONE group of one set, everything upstream held (same
   masters, same sky flat, same `-select` list, the registration PINNED via
   `--regdata=` so the transforms are bit-identical across arms — the flag
   exists for exactly this). Judged on: Siril `bgnoise` per channel, `-rejmaps`
   (what each algorithm actually discarded, and where), and the drift-axis star
   stations. A WIN moves the >50 branch or adds a gradient-conditioned branch;
   a NULL closes the question with a number and the ladder stays as-is.
   **k-MAD rides the same run as a third arm** — it is currently unexamined
   rather than rejected, and one extra arm costs one more stack.
2. **`-framing=max` + `stack -maximize -overlap_norm` at the compose** — the
   vendor pairs these and the repo uses neither. One knob at the compose only:
   `run_undistort_compose.sh`'s stack line, `stack r_s mean none -norm=addscale
   -weight=nbstack` → the same plus `-maximize -overlap_norm`, on an EXISTING
   member set so no frame is re-processed. Judged on the corner/edge background
   term the aug06 audit already characterized (`combine_corner_fail_
   investigation`: a combine-introduced +0.8-1.3% linear corner term inside
   ~500 px of the full-coverage corners, with three per-set controls and a
   matched july31 CLEAN control at 0.0-0.2% — the measurement and its geometry
   are already built). **Pre-registered risk, so it is not read as a free
   win:** `-maximize` changes the output CANVAS, so the arms are not
   pixel-comparable unless the comparison is made on WCS-matched sky boxes, as
   that audit's own reader already does. `-feather=` is explicitly NOT in this
   test — the follow-up entry records feathering as blending the step rather
   than removing it.
3. **Siril-native SIP undistort vs the darktable route** — one knob (the
   distortion mechanism), same set, judged on `seqtilt` off-axis + drift-axis
   stations + full-frame finals. The fitted lensfun entry's removal condition
   names exactly this ("a chain consuming the model another way — `register
   -disto=` with a trustworthy source"). Blocker history: astrometry.net SIP
   was measured-bad at this scale; the UNTESTED arm is Siril's own solver's
   SIP on the mildly-trailed july23 class.
4. **Native `platesolve -localasnet` on the mildly-trailed stack class** — the
   dead-end covers Siril's matcher on heavily-trailed july14 frames;
   roundness 0.80 data may match fine. If it does, the external solve route
   gains a native sibling (solve_field.py stays for the trailed class).
5. **`-opt` dark optimization vs matched darks (uncooled body)** — FAQ
   doctrine fork; A/B on one set, judged on dark-residual metrics (ties into
   the BACKLOG:`walking-noise` mechanism work). Low priority: our darks are
   same-night, shot at session-end temperature, which is the condition base
   doctrine says needs no optimisation.
   **POOLED MASTERS ACROSS NIGHTS RIDE THIS SAME FORK, and the decision rule
   is:** pooling is gated on the nights' masters measuring identical, judged
   on `noise_split.sh`'s structured term, and **per-session stays the
   default** until it is. The gate is currently SATISFIED on level and not
   yet decided: the three nights' pedestals agree to 0.1 ADU (`TOOLS.md`, the
   sensor-pedestal entry — cited, not restated) and their noise agrees within
   1%. Level agreement is not the whole test; the structured term is.
6. **Bayer-drizzle colour route for OSC** (a SHIPPED vendor script, not only an SPCC-page recommendation) —
   structurally incompatible with the darktable warp (drizzle needs CFA input;
   the warp needs demosaiced frames), so it becomes live only if test 1 moves
   undistortion into Siril. Chain dependency recorded.

## Sources

- siril.org/download/ + /download/2026-06-17-siril-1-4-4/ (stable version)
- gitlab.com/free-astro/siril @1.4.4: `<siril-repo>/scripts/OSC_Preprocessing*.ssf`,
  `src/core/settings.c`, `src/gui/stacking.c`, `src/gui/uifiles/siril.ui`
- gitlab.com/free-astro/siril-scripts (**the External Script Repository —
  user-contributed**, per its own README): `preprocessing/OSC_Preprocessing_
  Without{Flat,Dark,DBF}.ssf`, `DSA-OSC_Preprocessing_with_BGE_and_Undistort.ssf`,
  `preprocessing/osc-multi-night-stacking-v1.2.py` (the multi-night shape),
  `preprocessing/StorageFriendlyStacking.py`
- **The rig's own binary** — `siril-cli 1.4.4`, `help {stack,register,
  seqapplyreg,calibrate}` via an `.ssf`. This is the strongest class of source
  here for "does the option exist", since it is the installed tool answering
  rather than a doc describing a build; it is what settled `-overlap_norm`,
  `-feather=`, `-maximize`, k-MAD, `-opt=exp` and the `-cc=dark` sigma default.
- GitLab tree API `projects/free-astro%2Fsiril/repository/tree?ref=1.4.4` (the
  six shipped scripts) and `…%2Fsiril-scripts/…?recursive=true`
- siril.readthedocs.io/en/stable: preprocessing/{calibration,registration,
  stacking,conversion,drizzle}.html, astrometry/platesolving.html,
  processing/color-calibration/spcc.html, preferences/preferences_gui.html,
  Commands.html
- siril.org/faq/ · siril.org/2021/12/enough-with-dark-flats/
- discuss.pixls.us t/20991, t/35487, t/23972 (team statements, historical)
- pixinsight.net/dev (PI 1.9.4 build 1695, WBPP 2.9.0 announcements) ·
  pixinsight.com/forum threads 18148 (1.8.9/ESD-best), 18182 (WBPP 2.4.0 —
  the Auto rejection table + LN placement), 23775 (auto-CC default), 19079
  (min-weight intent), 25260 (1.9.3/Autocrop)
- pixinsight.com/doc/docs/{ImageWeighting,MARS,XISF-1.0-spec} · archived
  pixinsight.com/doc/tools/{ImageIntegration,ImageCalibration,StarAlignment}
  · gitlab.com/pixinsight/Reference-Documentation (LocalNormalization,
  CosmeticCorrection, Debayer, GradientCorrection pidocs) ·
  pixinsight.com/tutorials/{master-frames,sa-distortion}
- cloudynights.com t/769960 + t/843093, pixinsight.com/forum t/19589,
  star-watcher.ch (WBPP multi-session grouping — COMMUNITY consensus; the
  vendor announcement pages return 403 to this rig and were NOT read)
- deepskystacker.free.fr technical/FAQ (2026 archive) + github.com/
  deepskystacker/DSS (releases API — 6.2.2) · astropixelprocessor.com
  (features, Mabula mosaic tutorial part 2, downloads — 2.0.0-beta46)
- Repo records: `git show 3554aa3:datasets/july23/` (QA/audit/solves; session since archived —
  the records live in the archive + git history), `docs/dead-ends.md`
  (SIP/solver/weighting mechanisms); the 1.4.4 syntax audit this doc builds on
  is graduated into `TOOLS.md` Tier 1 (deep-dive retired — git history)

## Verdict / recommendation

The chain is doctrine-compliant at every stage Siril documents, usually at the
tool's own defaults (rejection selection, normalization, weighting-off,
cc=dark, debayer timing, 2-pass registration), and the master/calibration
doctrine agrees across ALL vendors checked (matched darks -nonorm, no bias, no
optimization, CC from the dark, CFA flat division, addscale lights). Where the
two vendors themselves disagree (GESD threshold 15 vs 50, CFA-drizzle-as-final
vs demosaic, weight-by-default vs no-weight, crop-before vs autocrop-after),
our chain sits on the Siril side by construction, and each fork is recorded
here rather than implicit. Two industry-reference capabilities remain genuine
Siril-side gaps, confirmed still open at WBPP 2.9.0: Local Normalization (§C
row, with the `-overlap_norm` precision correction) and PSF-Signal-Weight-class
weighting.

**The deviations, triaged by the strength of what backs them.** This is the
axis the standards-first rule cares about, and it is a different question from
"is there a paragraph about it".

*Justified by a measurement taken ON THIS RIG:* the per-set sky flat (star
specks 101 → 0 under winsorized vs pure median; cross-set application imprints
±6% L-R tilt vs 1-2% under a set's own; the flat's own odd component 4.8-19.4%
moonless / 16.8-22.6% moonlit with the plane's direction tracking the moon's
bearing to 23° where random scatters ~104°; GraXpert Division absorbs ~2/3 of
extended structure on a frame-filling field, which is why it is the fallback
and not the route). The external darktable undistort (a per-frame
astrometry.net SIP fit measured a LOSS: majFWHM 4.74 → 6.02 px). No
`-output_norm` on the undistort route (the min-max zero-point mechanism, with
`ANCLOC*`/`ANCSCL*`/`ANCREF` shipped in its place). 32-bit end-to-end
(~55-70% contrast retention at 16-bit; +21% fixed-pattern residual in a 16-bit
master dark). Mandatory `-cc=dark 3 3` (walking noise from uncorrected
fixed-position pixels under drift). The sub-stack multi-night compose (4.07 px
cross-night, §0.2 of the combine contract, vs the 0.14 / 0.19 px within-set floor
in `run_undistort_compose.sh`'s separation ladder).

*Resting on an INHERITED verdict never re-measured here — a hypothesis on this
rig until it is:* **the refusal of Siril's native solver for the current data
class.** The dead end was measured at roundness 0.615; the class actually on
the rig now reads 0.786-0.852, and the `-localasnet` probe is open
(BACKLOG:`native-solve-and-sip`, named test E4). The external route is right
for heavily-trailed data and UNTESTED as the *only* route for this one.

*Simply unexamined — the findings of this pass:* linear-fit and k-MAD rejection
(E1); `-maximize` + `-overlap_norm` at the compose (E2); and the 7-50
winsorized band, which §B has always labelled "our inference; docs state no
band" and which no measurement has ever supported or attacked.

*Recorded, but only in a ledger:* the compose-side background-matching survey
lives in `datasets/aug06/experiments.jsonl` and nowhere a reader would look.
Its feathering ruling is preserved in §B; its `-overlap_norm` half had no
ruling at all, which is why E2 exists.

**Where this repo is MORE rigorous than every pipeline surveyed — and where
its maintenance burden therefore sits.** No vendor script pins what this one
pins, because vendors ship a script while this ships a contract: `set32bits`
and `setcompress 0` in every emitted `.ssf` (both are PERSISTED siril
preferences, so an unpinned script inherits whatever ran last);
`-transf=homography` and `-interp=lanczos4` written out although both are
Siril defaults, so a version bump cannot silently change every stack; the
reference frame pinned with `setref lt 1`, because `-2pass` re-picks it from
image quality and that was MEASURED to change the output canvas across arms of
a one-knob test (4896×3616 vs 4887×3641); `-cc=dark 3 3` mandatory where the
vendor's own flatless script carries no cosmetic correction at all and its
main script carries hot-only σ3; and the rejection algorithm chosen by sub
count through a single shared function where every official script hard-codes
`rej 3 3`. Five guards exist to hold exactly these — `check_bitdepth.sh`,
`check_calibrate.sh`, `check_registration_pins.sh`, `check_stack_rejection.sh`,
`check_compose_flags.sh` — and that is the cost side of the ledger: each pin is
a thing that must keep being true, and the guards are what make it cheap
instead of a memory.

**PREMISES THIS AUDIT RESTED ON AND DID NOT TEST** (logged UNCHECKED, per
CLAUDE.md — convergence with another reader is not a discharge): that the
builders' emitted commands are what actually reaches siril at run time. **This
one is now PARTIALLY discharged, and the part that is not is named.** A
parallel session's `run_set_chain.sh sessions/aug06 set-01 --yes` (785e117)
produced `web/results/aug06/stack_set-01_full{,_wcs,_spcc}.fit`, whose headers
this audit read directly rather than taking the peer's word for:
`STACKNRM = addscale` with no output-normalization key, `BITPIX = -32`,
`STACKCNT = 500`, `REGREF = 1:aug06/groups_set-01/sub_01.fit` — a LIVE product
confirming the §B normalization and bit-depth rows from the artifact instead of
from the template. **It does NOT discharge the calibrate, undistort or
per-group registration rows**: that run took the RESUME path over five existing
sub-stacks (62 s wall-clock), so those stages did not execute, and by that
session's own measurement no from-raws wall-clock figure exists anywhere in
this tree. Those rows remain source-read only; that `-overlap_norm`'s estimator behaves on a drifting non-mosaic
sequence the way its one-sentence help implies; that the WBPP multi-session
shape is as the community describes it, the vendor pages being unreadable from
here; and that the weighting-off decision's "measured min-max-ramp soft-cull"
was measured on THIS rig — that record was cited, not opened, in this pass.

## Status

PROVISIONAL as doctrine mapping (source-verified 2026-08-31 against primary
sources; the version anchors and the Siril doctrine claims were re-verified,
not re-asserted, and the option list was probed on this rig's own binary).
Named tests E1-E6 not run. Repo-side numbers are EMPIRICALLY TESTED and cite
tracked records; §D's are archived readings (see the scope note).

## Graduation

- TOOLS.md: Tier 1's Local-Normalization gap sentence now names `-overlap_norm`
  and `-feather=` and says why neither closes it; the rejection ladder now
  records linear-fit and k-MAD as unexamined rather than absent.
- BACKLOG: named tests E1-E6 are PROPOSALS for the owner, not queue items —
  this pass wrote none (research sessions do not edit the queue).
- README reference-standard table: verified current at Siril 1.4.4 / PI 1.9.4 /
  WBPP 2.9.0 / DSS 6.2.2 / APP 2.0.0-beta46 (this doc is the audit trail).
- dead-ends.md: no changes (no entry contradicted; the SIP entry's scope is
  astrometry.net-index SIP, unchanged).
- CLOSED, no longer a graduation item: the `set16bits` removal condition, which
  has fired AND been applied AND been guarded (§B bit-depth row).
