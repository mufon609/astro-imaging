# Tier-B hardening — four items, executed

Guards, pins and one measured retest. Every claim below is a transcript from
this rig, not an argument. Where a check was added it was proven by BREAKING it
once; where a number is quoted, the command that produced it is named.

| item | outcome | commit |
|---|---|---|
| B1 registration pins | 20 commands in 10 files pinned; new per-COMMAND guard; recompose all-nil | `8d370dd` |
| B2 vignetting-off in the preflight | wired, unconditional (11.1 s); fire-tested; **found the restore path broken and fixed it** | `3072fd0` |
| B5 solve contradiction gate | exit 9 on refusal; `--central` semantics fixed at 3 sites; falsification fires, 0/69 false | `4d70455` |
| B3 aircraft rejection | **rejection CONFIRMED**; the specified test proved under-powered and a sensitive one replaced it | `e7cb2be` |

Nothing deferred. Three BACKLOG items removed entirely
(`unpinned-registration-defaults`, `aircraft-rejection-retest`,
`route-recommendation`'s first bullet), one `removal-conditions` row added for
the new solve gate and one re-checked and re-dated for the lensfun strip.

Two things worth reading even if you skip the rest, because both are cases of a
check that looked fine and was not:

- **B2's fire test found the remedy the new guard names does not work.**
  `install_lens_model.sh` reported `already installed` and exited 0 on a DB whose
  vignetting was back, because its idempotence test asked only about the
  distortion line and not about the distortion-ONLY enforcement it also
  installs.
- **B3's specified test cannot answer B3's question.** A full-depth product A/B
  dilutes a transient by the group size and again by the compose, to below what
  the difference can measure. It was executed, it is flat, and it is reported as
  under-powered rather than as a pass.

Read with: [`BACKLOG.md`](BACKLOG.md) (the register), [`TOOLS.md`](TOOLS.md)
(registration doctrine), [`docs/dead-ends.md`](docs/dead-ends.md) (the new
dilution entry), `datasets/july31/experiments.jsonl` (B3's ledger entry).

---

## B1 — the registration defaults are pinned, per COMMAND

**The hole.** `-transf=` (the transform model) and `-interp=` (the resampling
kernel) are both Siril DEFAULTS, and no generated `.ssf` pinned either. A tool
bump could therefore change the geometry and the resampling of every stack in
the repo with nothing in any record to show for it — the same shape as the
persisted `setext` / `setcompress 0` / `set32bits` state `check_bitdepth.sh`
already pins, except supplied by the VERSION rather than by the last run.

**The tokens came from the tool, not from memory** — `siril-cli` `help register`
/ `help seqapplyreg` on this rig's 1.4.4:

```
-transf= specifies the use of either shift, similarity, affine or homography (default)
-interp= ... no[ne], ne[arest], cu[bic], la[nczos4], li[near], ar[ea]
Clamping of the bicubic and lanczos4 interpolation methods is the default,
  to avoid artefacts, but can be disabled with the -noclamp argument.
```

So clamping has no ON switch: it is preserved by asserting `-noclamp` is ABSENT.
Doctrine pinned is `TOOLS.md`'s — homography, lanczos4 + clamp.

**Every site, and the decision at each.** 20 emitted commands in 10 files:

| file | command | pinned |
|---|---|---|
| `stack/siril/lights.ssf.tmpl` | `register pp_light -2pass` / `seqapplyreg pp_light` | transf / interp |
| `stack/run_pipeline.sh` (`_fits_lights`) | `register pp_light -2pass` / `seqapplyreg pp_light` | transf / interp |
| `stack/run_pipeline.sh` (`_fits_dualband`) | `register Ha_pp_light`, `register OIII_pp_light` | transf **+ interp** — one-pass register BOTH fits and resamples |
| `stack/run_undistort_pipeline.sh` | `register lt -2pass` / `seqapplyreg lt` | transf / interp |
| `stack/run_undistort_groups.sh` | `register s -2pass` / `seqapplyreg s` | transf / interp |
| `stack/run_undistort_compose.sh` | `register s -2pass` (star-pair arm) / `seqapplyreg s` | transf / interp — `seqplatesolve` (the shipped arm) has no transform or kernel of its own; the resample is `seqapplyreg`'s |
| `stack/compose.py` | `register ch -2pass` / `seqapplyreg ch` | transf / interp |
| `qa/noise_split.sh` | `register s -2pass` / `seqapplyreg s` | transf / interp — an instrument whose numbers must be stable across versions |
| `qa/coverage_probe.sh` | `register s -2pass` / `seqapplyreg s` | transf / interp — the map must be read at the SAME kernel the composed product carries; lanczos4 rings at a member edge, so a coverage threshold calibrated under another kernel does not transfer |
| `qa/run_frame_qa.sh` | `register c -2pass` (analysis-only) | **transf only.** It writes no product, but the model decides which frames find enough pairs to register and the registered/total ratio is a RECORDED metric. No `-interp=`: `-2pass` resamples nothing, so pinning a kernel there would assert a knob the leg does not turn |
| `stack/run_lunar_pipeline.sh` | `seqapplyreg pp_moon -interp=none` | already explicit — the ONE exemption, named in the guard |

Literals at every site rather than one shared constant: the emissions live in
bash printf strings, bash echo lines, a python string literal and a literal
`.ssf` — three languages, no symbol reaches them all. The guard asserts the
exact tokens instead, which gives the same protection.

**The guard** — `scripts/stack/check_registration_pins.sh` (mode 755), judged per
COMMAND, not per file (`check_bitdepth.sh` states its own per-FILE limit; this
one parses the emitted command lines out of every `.ssf` and `.ssf` emitter, so
each command is judged on its own). Prose that begins with the same word is
excluded structurally — a command is the verb, one sequence name, then flags
only, which rejects the lunar route's GUI instruction `register ALL images -> Go`
and the compose's log-description string without either needing to be reworded.

Floors (`>= 10` files, `>= 20` commands) are the canary: a parse that finds
nothing asserts nothing.

**Fire test — executed, three ways.** Each mutation, then the guard:

```
########## FIRE TEST 1: delete -interp=lanczos4 from run_undistort_groups.sh ##########
  PIN  scripts/stack/run_undistort_groups.sh: seqapplyreg s -framing=%s -prefix=r_: no -interp=lanczos4 — the resampling kernel rides Siril's default
FAIL: unpinned registration above — a Siril version bump changes those products silently
RAW EXIT CODE: 1

########## FIRE TEST 2: delete -transf=homography from the lights template ##########
  PIN  scripts/stack/siril/lights.ssf.tmpl: register pp_light -2pass: no -transf=homography — the transform model rides Siril's default
RAW EXIT: 1

########## FIRE TEST 3: add -noclamp to compose.py ##########
  PIN  scripts/stack/compose.py: seqapplyreg ch -framing=min -interp=lanczos4 -noclamp: passes -noclamp — clamping is the DEFAULT this repo keeps (lanczos4 rings on stars); there is no flag that turns it back on
RAW EXIT: 1
```

Restored, green: `OK: 20 registration commands in 10 files, every one pinned`,
exit 0.

`--selftest` proves the RULES independently of today's tree — 12 fixture
commands, 6 pinned and 6 unpinned/wrong, every verdict as stated. A guard whose
tree is clean is otherwise indistinguishable from a guard whose checks do
nothing.

**No behaviour change — the all-nil recompose proof.** aug06/set-01's five
sub-stacks, recomposed in scratch with EXACTLY the block
`run_undistort_groups.sh` emits today (`setref s 1` + both pins), differenced
against the shipped `stack_set-01_full.fit`:

```
register s -2pass -transf=homography
setref s 1
seqapplyreg s -framing=min -prefix=r_ -interp=lanczos4
stack r_s mean none -norm=addscale -output_norm -out=.../stack_pinned
```

Siril's own log confirms the reference and the clamp:
`Trial #1: ... choosing image 1 as new reference` (so the `setref s 1` pin is a
no-op on this data and the pins are the only knob), `Interpolation clamping
active`.

`isub` + `stat`, **both directions**, so a float clip at one sign cannot hide a
difference:

```
shipped - pinned :  Statistics computation failed for channel 0 (all nil?).
                    Statistics computation failed for channel 1 (all nil?).
                    Statistics computation failed for channel 2 (all nil?).
pinned - shipped :  (identical — all three channels nil)
POSITIVE CONTROL (shipped x 1.01 - shipped):
  Red   layer: Mean: 0.2, Median: 0.1, Sigma: 1.1, Min: 0.0, Max: 569.9
  Green layer: Mean: 0.8, Median: 0.7, Sigma: 1.4, Min: 0.6, Max: 655.3
  Blue  layer: Mean: 0.5, Median: 0.4, Sigma: 1.2, Min: 0.2, Max: 578.1
```

The pixel data is identical; the file md5s differ only because the shipped
product also carries the post-stack provenance stamp — `REGMODEL`, `REGUNDIS`
present only on the shipped file, plus `DATE` and `PIPEREV`. Nothing else in the
headers differs, geometry and BITPIX included (4907x3598, -32).

So Siril 1.4.4's defaults ARE homography + lanczos4 + clamp today. That is
precisely why the pins are worth having: the equality is a measurement of this
version, not a guarantee about the next.

**BACKLOG:** `unpinned-registration-defaults` removed entirely.

---

## B2 — the preflight proves vignetting is OFF, every set

**The hole.** `verify_lens_card.py` existed and passed, and nothing called it.
The distortion-only correction set is enforced in the lensfun user DB
(darktable ignores a style's lens `op_params`), and `lensfun-update-data`
OVERWRITES that DB — so the strip was machine-local state a routine tool update
reverts, re-checked only by a human remembering to.

**What changed.** `lens_preflight.py --require-profile` now runs it, via a new
`prove_vignetting_off()` that delegates whole to the existing tool. Ordered LAST
of the three checks, because it is the only one that costs a render pair of its
own — the two cheaper checks catch the same `lensfun-update-data` event and stop
before this one is paid for.

Invoked `--from-frame`, not `--session/--set`: the fixture then takes its optics
AND its card geometry from the frame this preflight has already proven uniform
across the set, so it works before `acquisition.json` is seeded and cannot
disagree with the frames.

**Cost, measured:** 11.1 s standalone on this rig's 6064x4040 frames; the whole
`--require-profile` preflight goes 14.4 s -> **25.5 s**. Seconds-class against a
run that already renders one raw twice, so it is unconditional.

**Fire test — executed.** The fitted lens's `focal=70 aperture=4.0`
`<vignetting>` pair was reinstated by hand into the live lensfun user DB
(`mil-nikon.xml`, the block carrying the `astro-imaging fitted:` marker):

```
lens_preflight: the distortion-only proof FAILED — darktable's lens correction is not the set this chain is built on:
verify_lens_card: 'NIKON Z6_3' + 'NIKKOR Z 24-70mm f/4 S' @ 70.0mm on a 6064x4040 card
  grid control: module FIRES (Siril sigma 16031.1)
  uniform card: centre median 30002.0; worst corner corner_TR differs by 4219.000 ADU (tol 1.0)
  uniform card lensdist vs nodist: differs
verify_lens_card: FAIL — corner median differs from centre by 4219.000 ADU at corner_TR.
  Vignetting is back in darktable's path: re-run scripts/darktable/install_lens_model.sh
########## EXIT CODE: 1 ##########
```

**The load-bearing part of that transcript is what did NOT fire.** In the same
run:

```
  pinned model OK: NIKKOR Z 24-70mm f/4 S@70 matches the live DB
  darktable PROVES it corrects this set (lensdist vs nodist: Siril stat max 65535, not a no-op)
```

Both existing checks passed while darktable was applying a 14% photometric
corner correction. A vignetting-corrected frame IS warped, so the
warp-happened proof cannot see it, and the coefficients were untouched, so the
pinned-model assert cannot either. That is the measurement that justifies the
third check rather than an argument for it.

**A real defect the fire test found: the restore path did not restore.** The
documented remedy — the one the new guard's own message names —
no-opped:

```
install_lens_model: already installed for Nikkor Z 24-70mm f/4 S @ 70mm (mil-nikon.xml)
EXIT: 0
```

...with the injected `<vignetting>` still live. Its idempotence test asked only
about the distortion line, not about the distortion-ONLY enforcement it also
installs. Fixed: the test now also requires the strip to hold, and the repair
says what it is doing. Advice that no-ops in exactly the state the guard reports
is worse than no advice — and this file's own header already records one
incident of "the DB could not be restored by any documented invocation".

```
install_lens_model: coefficients already pinned, but 2 live <vignetting>/<tca> entries are back
  in Nikkor Z 24-70mm f/4 S — re-stripping (darktable applies its DEFAULT correction set,
  and only this DB chooses otherwise)
install_lens_model: Nikkor Z 24-70mm f/4 S @ 70mm — replaced a=0.00350093 b=0.01453356 c=0.00043983
  stripped 2 vignetting/tca entries — distortion-only holds
```

**Green restored:**

```
lens_preflight: 500 frames, optics UNIFORM
  pinned model OK: NIKKOR Z 24-70mm f/4 S@70 matches the live DB
  darktable PROVES it corrects this set (lensdist vs nodist: Siril stat max 65535, not a no-op)
  distortion-only VERIFIED: grid control fires (Siril sigma 45398.0), uniform card worst corner
    corner_TL 0.000 ADU from centre (tol 1.0) — no vignetting in the path
########## EXIT: 0 ##########
```

The grid sigma returns to its pre-injection 45398.0 and the DB differs from its
backup on ONE line — the marker's own provenance stamp, which now records that
this install re-stripped 2 entries.

**BACKLOG:** `route-recommendation` bullet 1 removed (the item keeps its second
bullet, the per-lens re-derivation at the next new lens/body/focal). The
`removal-conditions` row for the vignetting/tca strip is re-checked, dated, and
now records that the re-verification is automatic.

---

## B5 — the blind solve must not contradict its own hints

**The incident, re-read from the record rather than from the prompt.**
`web/results/aug09/solve_stack_july31+aug06+aug09_full.json`:

```
"central": 0.5, "position_hint": null, "position_hint_source": "header",
"attempt": "cached + blind",
"ra_deg": 6.0319, "dec_deg": -65.1006, "scale_arcsec_px": 12.9602,
"logodds": 22.32, "parity": "MIRRORED vs sky",
"injected": ".../stack_july31+aug06+aug09_full_wcs.fit"
```

The hinted attempt failed on the seam-contaminated framing=max canvas; the blind
fallback won and the WCS was injected. The hint it contradicted is in the
product's own header, and it is genuinely independent of this solve — the
composed stack inherits the already-solved MEMBERS' astrometry, and siril writes
the WCS field centre into `RA`/`DEC` on save. Verified exactly:

```
image-centre from WCS: 309.77441286524606  41.69700510110738
header RA/DEC        : 309.774412865246     41.6970051011074
```

**Why the solve is the only place to stop it.** One step downstream, siril SPCC
ran to COMPLETION on that WCS and produced plausible K factors (R 1.000 G 0.592
B 0.817, "1790/5153 stars kept") instead of failing. A confident falsehood
therefore reaches the deliverable unchallenged.

**The `--central` semantics.** It was a HALF-WIDTH fraction
(`|x - w/2| > central*w`), so `--central=0.5` kept the whole frame — the one
invocation reached for during the failed union solve excluded nothing while
reading like a recovery attempt. Both docstrings always described a fraction of
the FRAME. Shipped: fraction-of-frame (`|dx| <= frac*w/2`), values outside (0,1)
refused, and the retained box printed in pixels every run so a no-op is
impossible to mistake:

```
--central=1.0   exit 1 | solve_field: --central=1 is not a fraction of the frame in (0,1).
                         1.0 keeps everything, so it is a no-op that reads like a restriction
                         — pass no --central instead. (--central=0.5 = the central HALF of each axis.)
--central=0     exit 1 | (same)
--central=1.5   exit 1 | (same)
--central=0.4          | [solve_field] 200 stars via sep (SExtractor core)
                         (central 0.4 of frame = the middle 1960x1442 px of 4901x3606)
```

Aligned at all three sites: `solve_field.py`, `finish_render.sh`, and
`web/serve.py` (both stage hints; the UI clamp upper bound moved 1.0 -> 0.95, so
the UI cannot ask for the refused no-op).

**The gate.** In `solve_field.py`, evaluated on the accepted match BEFORE
inject/json/record — a refused solve leaves nothing behind for a later stage to
pick up, which is exactly how the incident propagated.

| leg | threshold | rationale (in the code, at the constants) |
|---|---|---|
| POSITION | separation > **2x** the hint radius | The radius is the declared uncertainty. Every hinted solve in this corpus lands within 0.27 deg of a 15 deg hint; the false one sat 115.4 deg out, 7.7x the radius. Two orders of magnitude of separation, not a tuned number. |
| SCALE | outside **+-20%** of the header nominal | Budgeted from mechanism: integer-mm EXIF focal (70+-0.5mm = +-0.7%), XPIXSZ rounding, infinity-vs-marked focal, and the TAN projection's own centre-to-corner ratio across a 28.6 deg field (1/cos^2(14.3 deg) = 1.066). Those sum under 10%; 20% doubles it. |
| LOGODDS | **warning** below 100 | Not a refusal — nothing contradicts a solve that had no hint, and a genuinely hard field may land low. 100 is this file's own confident-match threshold. |

The gate reads the hint that EXISTED (CLI or header), not the winning attempt's —
those differ exactly in the case the gate is for (`position_hint: null` with
`position_hint_source: header`). The solver's own size hint stays deliberately
wide (0.6-1.5x) so a bad header cannot exclude a correct solve; the gate is
tighter on purpose, because bounding where to LOOK and judging whether the
ANSWER contradicts the header are different questions. `header_scale()` is now
the single source both read.

Escape hatch: `--accept-contradiction` (proceeds, and records
`contradiction_accepted: true`). Exit **9** — a user decision in the chain's gate
family (2/4/5/6/7/8), distinct from exit 1 "no solution at all".

**Falsification case — executed.** The corpus stack WITHOUT `--central`, solved
to a scratch `--inject` path. It reproduced the incident exactly (RA 6.032 Dec
-65.101, 12.96 arcsec/px, logodds 22 — the recorded values to three decimals)
and then refused:

```
[solve_field] position hint from header: RA 309.77 Dec +41.70 r15 deg (unverified — falls back to blind on failure)
[solve_field] 400 stars via sep (SExtractor core)
[solve_field] attempt [cached]
[solve_field] index scales [13..19] | scale hint: 10.5-26.3 arcsec/px | position hint RA 309.8 Dec +41.7 r15 deg
[solve_field] attempt [cached + blind]
[solve_field] SOLVED: RA 6.032 Dec -65.101 scale 12.96 arcsec/px logodds 22
[solve_field] parity: det(CD) +1.30e-05 -> displayed image is MIRRORED vs sky
[solve_field] WARNING: logodds 22.3 is below the confident-match floor of 100 — this match is
    FLOOR-CLASS. Every real solve in this corpus posts 103-574; the one measured FALSE solve
    posted 22.3. Treat the position and scale below as unconfirmed.

solve_field: REFUSING this solution — it CONTRADICTS the hints this file already carried:
    POSITION: solved centre RA 6.032 Dec -65.101 is 115.4 deg from the header hint
              RA 309.774 Dec +41.697 (radius 15 deg) — past 2x that radius (30 deg)
    SCALE:    solved 12.960 arcsec/px is 0.740x the header-derived 17.503 arcsec/px
              — past the +-20% band (14.002-21.004)
    accepted attempt [cached + blind], logodds 22.3, 400 stars, no --central
    Nothing injected, no record written. A blind fallback can ship a confident falsehood —
    SPCC ran to completion on one and produced plausible K factors — so this stops here.
    Options: give the right hint (--ra/--dec [--radius-deg]); restrict detection to the clean
    middle (--central=<frac of the frame>, ...); or take it deliberately with
    --accept-contradiction.
EXITCODE=9
```

Verified afterwards: no WCS was injected, the recorded incident JSON is
byte-identical to its pre-run backup (the record path derives from the INPUT, so
the gate exiting before the write is what protects it), and the shipped
`_wcs.fit` was never touched.

**Zero false fires — the replay.** The gate's REAL functions
(`contradictions`, `POSITION_RADIUS_FACTOR`, `SCALE_TOLERANCE`,
`LOGODDS_FLOOR`) imported and replayed over every recorded solve in the repo —
replaying a re-implementation would prove nothing about the code that ships:

```
gate: position > 2x hint radius; scale outside +-20% of header nominal; logodds warning below 100
replayed 69 recorded solves

WOULD REFUSE: 1
  aug09/solve_stack_july31+aug06+aug09_full.json
      POSITION: solved centre RA 6.032 Dec -65.101 is 115.4 deg from the header hint
                RA 309.774 Dec +41.697 (radius 15 deg) — past 2x that radius (30 deg)
      SCALE:    solved 12.960 arcsec/px is 0.740x the header-derived 17.503 arcsec/px
                — past the +-20% band (14.002-21.004)

WOULD PASS:   68   (of which 15 had a position hint to check and 53 had none)

logodds WARNING (not a refusal): 1
  aug09/solve_stack_july31+aug06+aug09_full.json: 22.3
```

One refusal — the known-false solve, on BOTH legs — and 68 clean. The 68 real
solves span 0.969-0.976 of the header nominal (a -2.4 to -3.1% systematic, 8x
inside the band) at logodds 103-574.

**Stated scope limit.** 53 of the 68 are per-member sub-stacks. Their headers
carry `FOCALLEN`/`XPIXSZ` but no `RA`/`DEC` (checked:
`sessions/aug06/work/groups_set-01/sub_01.fit`), so on those only the SCALE leg
and the logodds warning are live. The position leg needs a product whose header
carries a pointing — which every composed stack does, and which is the class the
incident belongs to.

**Registered** as a divergence with its removal condition (retires when the
solver itself refuses a solution contradicting a supplied hint) in the same
commit.

---

## B3 — prove the aircraft actually rejected

**VERDICT: rejection CONFIRMED. The ratified keep is verified free depth at this
route.** Ledger entry `aircraft_rejection_retest_july31_set03` in
`datasets/july31/experiments.jsonl`.

**Route and group size, stated — the argument's denominator.** Ratified: 500
frames, groups route, 5 groups of 100. Control: 492 frames (`DSC_5151..5158`
excluded), 5 groups of 2x99 + 3x98. Both arms take the same master dark, the
same `skyflat_set-03` (NOT rebuilt — reusing it keeps the 8 frames as the only
knob), GESD `rej g 0.3 0.05` per group (98/99/100 all sit in the >50 GESD band),
`-framing=min`, and a 5-member plain-mean compose with no rejection. The control
went to its own `--out`; nothing shipped was touched.

Products: 4901x3606 STACKCNT 500 LIVETIME 1250.0 against 4908x3619 STACKCNT 492
LIVETIME 1230.0 — a 20.0 s difference, exactly 8 x 2.5 s.

### The specified test was executed, and it is UNDER-POWERED

The item's own closing test — difference the two full-depth products — is flat.
On the common canvas (4650x3306), 88 boxes of 400 px read box means 33.1-33.3
ADU, strongest/median **1.01**; the whole difference is a uniform pedestal
(R 13.9 / G 33.1 / B 23.1) from the two builds' independent `-output_norm` level
anchors, with no localized excess anywhere.

That is not a pass, because it is not a discriminating measurement. Measured, in
this order:

- **The trail's per-frame amplitude** (Siril `stat`, 40x40 boxes stepped along
  the audit's own geometry). On `DSC_5155` the on-trail box reads mean 1229.3 /
  sigma 293.4 / max 3195 against the SAME box on the aircraft-free `DSC_5100` at
  1138.0 / 23.0 / 1566; the along-track neighbour 1215.7 / 251.1 / 2786. The
  boxes at +-0.4 of the trail length, and every y-flipped box, read the clean
  frame's level — so the geometry AND the coordinate convention are settled by
  the data rather than assumed. Sky ~1140 ADU, per-frame `bgnoise` ~12 ADU: a
  trail pixel is a **60-170 sigma** per-pixel outlier, ~766 ADU above sky on the
  box-flux average.
- **Coverage per pixel, the ratified keep's own mechanism, now measured.** The
  audit's centroids move ~820 px/frame (full scale) against a ~740 px trail
  length, so the trail crosses each sky pixel in **~1 frame**. At groups@100
  that is 1/100 against GESD's 0.30 outlier-fraction cap.
- **Therefore the dilution.** Even a totally unrejected trail contributes
  766/100/5 = **1.5-4.1 ADU per trail pixel** to the final product, which spread
  over a 400 px box is 0.02-0.06 ADU against the measured 0.2 ADU box-to-box
  spread. A flat product difference is equally consistent with rejection and
  with none.

Recorded as a mechanism entry in `docs/dead-ends.md`: audit rejection where it
HAPPENS, not after two stages of dilution.

### The discriminating measurement

**Siril's own rejection map, and a matched control.** `stack ... rej g 0.3 0.05
-rejmaps` on group 4 — the group carrying the crossing, which sits at positions
62-69 of its 100 frames — writes the per-pixel record of which samples GESD
discarded. The same was run on the same group's 92 frames with the aircraft
removed. One knob.

Rendering group 4's map alone is NOT evidence: the control map carries diagonal
streaks too (drift-dragged sensor-fixed defects — the registry's `walking-noise`
class). It is the DIFFERENCE of the two maps that isolates the aircraft, and it
contains **only** the aircraft's twin-trail segments, stepping across the canvas
in eight consecutive positions; everything else sits at the difference's own
noise.

Two independent confirmations that the map is being read correctly:

- its median is **-114.0 ADU**, exactly the arithmetic scale step between a
  92-frame and a 100-frame denominator ((2/92 - 2/100) x 65535 = -114.0), which
  calibrates the map for free;
- group 4's own map reads median 1310.5 = **2.00 frames** and max 19660.5 =
  **30.00 frames**, exactly GESD's 0.30 outlier-fraction cap.

The track's amplitude is **+1 frame** (655.35 ADU) — matching the ~1-frame-per-
pixel coverage exactly. It is invisible to any grid or whole-frame statistic
(at +1 frame against the map difference's 269 ADU sigma it sits inside the 2.9
sigma noise tail, and a 150 px grid scan returns only frame-edge effects), which
is why it was located by block-averaging the map difference 16x16 — in-house
code doing nothing but LOCATING, so that Siril could measure there.

**The on-track residual.** The 100-frame and 92-frame stacks share a canvas, so
they difference directly. 60x60 boxes at six points on the track the rejection
map identified, against perpendicular controls at +-200 and +-400 px:

```
whole-frame difference mean 4.50 ADU (the two stacks' own -output_norm anchors)
  ON-TRACK :  4.30  4.40  4.30  4.50  4.40  4.20    mean 4.35
  perp +200:  4.40  4.50  4.30  4.50  4.40  4.30    mean 4.40
  perp -200:  4.40  4.40  4.50  4.40  4.50  4.30    mean 4.42
  perp +400:  4.40  4.40  4.30  4.30  4.40  4.40    mean 4.37
  perp -400:  4.60  4.40  4.50  4.50  4.50  4.40    mean 4.48
```

On-track minus off-track = **-0.07 +- 0.08 ADU**. And this test IS sensitive: an
entirely unrejected trail would raise a 60x60 on-track box by ~0.9 ADU (7.7 ADU
per trail pixel in the group mean, 11.6% box fill) against a +-0.2 ADU spread.
So rejection removed **>= 91%**, and the result is consistent with 100%.

**Declared deviation.** The rejection-map and on-track probes ran WITHOUT the
darktable warp. The warp is a geometric resample and cannot change whether a
60-170 sigma sample is an outlier among 100; everything bearing on rejection —
the same 100 frames, the same masters, the same `calibrate` command, the same
rejection clause, the same registration model — is what the chain runs. The
full-set A/B, which DID include the warp, is consistent.

**BACKLOG:** `aircraft-rejection-retest` removed entirely. Control stack and the
`set-03ctl` staging deleted after the verdict, per the item's own instruction.

---

## Guards, after

```
check_bitdepth               PASS
check_calibrate              PASS
check_siril_invoke           PASS
check_stack_rejection        PASS
check_registration_pins      PASS
check_registration_pins --selftest   OK: 12 rule cases (6 pinned, 6 unpinned/wrong) all verdict as stated
lens_preflight.py --selftest         SELFTEST PASS
```

`check_bitdepth.sh` caught the new guard on its own discovery rule (any file
naming `.ssf` on a non-comment line must emit `setcompress 0`) — it names `.ssf`
only in its search patterns and generates none, so it joined that guard's stated
exemption list with its reason, which is what the list is for.

## What was NOT done, and what is left behind

Nothing was deferred; all four items are closed with executed evidence.

Two things the next session should know:

- **92 `datasets/` records were already uncommitted when this session started**
  (the earlier rebuild's per-set state). Nothing here touched them — verified,
  no tracked dataset record has an mtime inside this session — and they are
  deliberately left out of these four commits. They still need a decision.
- **B5's gate is untested on a set whose header carries no pointing.** 53 of the
  69 replayed solves are per-member sub-stacks with `FOCALLEN`/`XPIXSZ` but no
  `RA`/`DEC`, so only the scale leg and the logodds warning are live there. That
  is stated in the `removal-conditions` row rather than left to be discovered.

B3's scratch (rejection maps, their difference, the on-track stats) lives under
`~/.cache/astro-imaging/b3_*` and is regenerable from the commands in the ledger
entry; the control stack and the `set-03ctl` staging were deleted after the
verdict, per the item's own instruction, with the 500 raws verified intact.
