# How combines actually worked here, and what the standard architecture is

Two questions, answered from the record rather than from memory: **when did this
start**, and **what is the industry-standard way**. Every claim below is either
recovered from git (with its commit) or measured this session (with its
instrument). Nothing is inferred from the current state of the tree.

---

## 1. The history — what the record actually says

### 1.1 Cross-night combining has been attempted ONCE, and it failed

Searching every path that has ever existed in this repository for a product
spanning two sessions returns exactly four records, all one product and its
revoked recrop:

```
datasets/aug06/set-03/qa_work/solve_stack_j31-3+a06-3_cov28.json
datasets/aug06/set-03/qa_work/solve_stack_j31-3+a06-3_cov28i450.json
datasets/aug06/set-03/qa_work/spcc_set-03_j31-3+a06-3_cov28.json
datasets/aug06/set-03/qa_work/spcc_set-03_j31-3+a06-3_cov28i450.json
```

Built 2026-08-08. That is the six-member july31+aug06 twin — one of the two
products the owner failed.

**Every other combine in this repo's history is WITHIN a single night:**
july14's `set-01+02` (min and max), `set-01+02+03`, `set-04+05`, and the five-set
`cov25frame`; july23's `set-01+02`; july31's `set-01+02+03+04`.

So the premise that a previous method combined *different nights* without issue
does not hold. **What worked was combining SETS WITHIN a night.** Cross-night has
never had a working demonstration to return to.

### 1.2 Multi-session accumulation became doctrine one day before its first attempt

`cd778e5` (2026-08-07 21:53) ratified *"multi-session accumulation is standing
practice — full sets combine, the FINAL pass stacks the best N%"*. The first
cross-night product was built 2026-08-08 07:49, ~10 hours later. The doctrine
records a user-ratified *intent*; it was never a report of a capability that had
been exercised.

### 1.3 Every combine that was ever accepted shared ONE distortion model

| combine | night(s) | models across members | framing | outcome |
|---|---|---|---|---|
| july14 `set-01+02`, `set-01+02+03`, `cov25frame` (5 sets) | july14 | ONE (the july14 fit) | min and max | built; **value UNCONFIRMED** at the time (§1.4) |
| july23 `set-01+02` | july23 | ONE | min | **user-flagged corner defect** (chroma class) |
| july31 `set-01+02+03+04` | july31 | ONE (july14 fit, inherited with recorded provenance) | min | **PASSES — user's eyes** |
| aug06 `set-01+02+03` | aug06 | **THREE** (per-set fits) | max + covcrop | **FAILS — corner star doubling** |
| aug06 `j31-3+a06-3` | **two nights** | THREE + the inherited july14 model | max + covcrop | **FAILS** |

The single constant of every combine that was ever accepted is **model
homogeneity**. That is consistent with the root cause already measured (members
warped under different models disagree 2.99 px at the composed corner against
0.93 px for the same pair under one model), and it is now also consistent with
what the *tools* assume (§2.3).

### 1.4 The combine's value was flagged unconfirmed from the very first commit

`9ab337d` (2026-07-18), the commit that created `run_undistort_compose.sh`:

> *"Measured on set-01+02+03 (arm base rig): the combine RUNS but its VALUE is
> UNCONFIRMED. — field is rotation-limited: 57% (single) → 42% (2-set) → 24%
> (3-set, 5.9 Mpx); DEPTH NOT MATERIALISING: bgnoise flat across 369→1032 frames,
> star density down; washed-out renders = blended per-set gradients."*

Recovered july14 records also show an early corner signal tied to framing —
`star_shape_set-01+02_max.json` off-axis aberration **0.91 px** against
`_min.json`'s **0.16 px** on the same two sets. (Both numbers come from
`seqtilt`, which this session has since measured **blind** to the star-doubling
defect — so they bound the framing question, not this one.)

### 1.5 Onset, stated precisely

- **Last combine accepted by the owner:** july31 four-set, built 2026-08-07 00:05,
  one model across all 17 members, `-framing=min`.
- **First combine that failed:** aug06 `set-01+02+03_full`, built 2026-08-08
  07:44, three models across 13 members, `-framing=max` + coverage crop.
- **What separates them, measured:** the per-set model adoption. The aug06
  *pinned-arm* members — same frames, same chain, built before the adoption —
  compose corner-clean by eye; framing was eliminated separately (the min-framed
  aug06 union smears equally).
- **What is NOT a regression:** cross-night combining. It never worked, because
  it was never done.

---

## 2. The standard architecture, and where this repo diverges

Stated first, per the standards-first rule, with sources.

### 2.1 What the industry does

For coadding exposures taken at different times, pointings and rotations, the
standard is **per-image astrometric distortion, then resampling onto a common
output WCS**:

- **SWarp** (Bertin, Astromatic) is the reference implementation and the
  lineage behind SDSS, CFHTLS, DES and Pan-STARRS coadds: each input carries its
  own WCS *including* a distortion representation (TPV/SIP), and SWarp resamples
  every input onto one output grid using that solution.
- **PixInsight**: `ImageSolver` per image + `StarAlignment` with distortion
  correction (2-D surface splines), or astrometric normalisation.
- **Astro Pixel Processor**: per-frame lens-distortion modelling estimated from
  the star field.

The common property: **distortion is derived from the SKY, per exposure. There
is no shared instrument model for members to disagree about.** The failure this
repo hit is structurally impossible in that architecture.

### 2.2 Where this repo diverges, and why

The route fits ONE lens model from a set's frames (hugin), installs it into the
lensfun user DB, warps with darktable, and only then registers by stars. The
divergence was adopted for a measured reason — a far-drifting untracked set
cannot be registered by one homography, and the internal solver could not match
single ultra-wide **trailed** frames. Both remain true for FRAMES.

**But two of its supporting beliefs have now been measured false for MEMBERS:**

- **Siril's solver does handle this class on stacked members.** MEASURED:
  `seqplatesolve -order=3` solved both aug06 members, 388 and 371 matched stars,
  residual σx/σy ≈ 0.9 px, centres agreeing with astrometry.net to 0.001°, and
  wrote `RA---TAN-SIP` + `A_ORDER 3` into each member's own header. The old
  belief was measured on single trailed frames and had silently widened.
- **A fitted model is not reproducible to better than ~3 px** in the outer field
  (four independent fits of one set span 0.36–6.30 px), which is the scale of the
  2.99 px defect it is supposed to fix.

### 2.3 The queued removal-condition test — run, and REFUTED as invoked

`BACKLOG:native-solve-and-sip` has long queued *"Siril-native SIP undistort vs
the darktable warp … this is the fitted-lens-model removal-condition test"*. It
was never run, and its stated acceptance measures (`seqtilt` off-axis, drift-axis
stations) are both now measured blind to this defect. Re-run here on the
instrument that can see it:

| arm | centre | mid | outer | corner |
|---|---|---|---|---|
| shipped route (lensfun warp, homography registration) — the control | 0.29 | 0.63 | 2.10 | **2.99** |
| each member undistorted by ITS OWN astrometric SIP, then composed | **3.99** | 6.42 | 6.19 | n/a |
| ONE member warped by its own SIP, composed against its own unwarped self | 8.50 | 9.45 | 6.76 | n/a |

**REFUTED as invoked, and the third row explains why:** a SIP polynomial is not
identity-preserving on its own. `register -disto=` is designed for a sequence
that SHARES one plate solution, where the absolute warp is common to every frame
and cancels. Applying different members' solutions independently does not cancel.

**Siril's own design therefore assumes one optical state per sequence** — the
same one-model-per-combine-family pattern, now confirmed as the tool's
assumption rather than this repo's invention.

### 2.4 The actual gap

Nothing installed performs the standard operation — resampling each exposure onto
a common output WCS using its own full solution (CD matrix *and* distortion).
Siril has no such command. **SWarp is packaged for this distro (2.41.5-3) and is
not installed**; python `reproject` is likewise absent.

---

## 3. What this means for the road

Three routes, with what is measured about each. **No route is adopted here** —
this is the evidence for the decision.

**R1 — One model per combine family (same-night).** Matches what every accepted
combine here already did, and matches Siril's own sequence assumption (§2.3).
MEASURED cost: 0.93 px within aug06 against july31's 0.35 px, and it costs each
set its own state (set-01 off-axis 0.48 → 0.82 px). MEASURED limit: **does not
cross nights** (4.07 px under a shared model).

**R2 — Corner-true per-state fits.** The route the last directive set. Now
blocked twice over: no fit reaches the corner criterion, corner correspondences
are bad SIFT matches rather than victims of pruning, and the fit's own
reproducibility (±3 px) is the size of the defect. It also asks the fitted-model
architecture to do something the industry does not ask of it.

**R3 — Astrometric resampling (SWarp or equivalent).** The industry standard.
It dissolves the failure by construction: no shared model, every member mapped to
the sky by its own solution, cross-night identical to same-night. It is the only
one of the three with a *documented* answer to multi-night combining. Costs: a
new tool in the chain, a rewrite of the compose stage, and the undistort stage's
role changes (the lens warp may become unnecessary for MEMBERS while remaining
necessary for FRAMES within a set). Nothing about it is measured on this data yet
— the honest status is **unmeasured candidate**, and the first test is cheap:
install SWarp, resample the two aug06 members that currently disagree by 2.99 px
onto one WCS, and read the same instrument.

The measured facts that constrain the choice:

- every accepted combine here used one model;
- cross-night has no working precedent in this repo;
- the tools' own design (Siril) assumes one optical state per sequence;
- the industry does not use a shared instrument model at all — it solves each
  exposure against the sky.
