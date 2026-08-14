# Oracle handoff — engagement 1 → engagement 2

> **PM ADDENDUM, added when this was moved out of a session-scoped scratchpad into
> the repo. The body below is the outgoing Oracle's, unedited. Two facts moved
> between it being written and it being landed:**
>
> - **§1 and §5 call `d5`'s cloud measurement "in flight". It is COMPLETE** — five
>   commits, pre-registered with no result attached, then corrected twice by its own
>   author. **Net: the signature is alive at `Z_bg +4.05`, n=15, which is a FLOOR
>   rather than an estimate** (the 15 frames were flagged on `nstars` only, so their
>   `bg` z was *below* the cull threshold — conditioned against the effect). The
>   headline `+6.07` was **circular**: `recipe.json`'s `stack.why` records the cull
>   criterion as *"defect-side robust z >= 3.5"* on **`bg` and `nstars`**, 44 of 44
>   flagged on `nstars` and 29 of 44 also on `bg`, so the positive control was the
>   output of a threshold on the two fields under test. `Z_nstars` is withdrawn
>   entirely. **And the bounding fact is a NAMING limit, not a validation one:
>   nothing establishes by OBSERVATION that those frames contain cloud.** It DOES
>   meet the positive-control rule — the 15 were caught by the z-flagger on
>   `nstars` ONLY, so `bg` did not select them, and `bg` fires on them at +4.05:
>   non-circular data on which it must fire. **What is missing is the CAUSE. So it
>   is VALIDATED as detecting background elevation co-occurring with star loss and
>   NOT as detecting cloud** — thin cloud, haze, moonrise, dew and a light-dome
>   change are not separable on this corpus. **Naming it "the cloud signature" is
>   this repo's own recurring failure one level out, and the fix is the NAME rather
>   than a demotion to advisory.** The `+4.05` is a FLOOR and must not be wired as a
>   threshold.
>   A 673-file sweep for an independent sky observation found one, in the LUNAR
>   class, where `bg` and `nstars` are meaningless — which is what makes the
>   deep-sky NO a measured absence rather than a search that could not fire.
> - **The pedestal is no longer assumed.** MEASURED **1007.2 ADU** (Siril `stat`,
>   328-frame master dark at the lights' 2.5 s; 1007.2/1007.3/1007.3 across three
>   nights; EXIF `BlackLevel` **1008**; an independent astropy read gives 1007.24).
>   The 1024 that had been assumed was **mine**, and it understated the sky term by
>   62%. Dilution of a raw `bg` fraction is **24×**, not the ~39× I claimed — the
>   design conclusion is unchanged (the signature must operate on pedestal-corrected
>   `bg`), only the magnitude moved.
>
> **Everything else below was accurate when written and I reproduced the MEASURED
> items independently. The MECHANISM items are the outgoing Oracle's derivations and
> are explicitly hypotheses — that tagging is the most valuable thing in this file
> and it is the first thing a summariser drops.**

**Read `prompts/ORACLE_TEMPLATE.md` first.** As of `9bbf6ea` it carries the search
strategy (internal vs external claims), six failure modes, six PM obligations and
the corrected knowledge-base table. **This file deliberately does NOT repeat any of
that.** It carries only what a document cannot: live state, negative results, and
which of my claims are inference rather than measurement.

---

## 1. TEAM STATE AT HANDOFF

| session | role |
|---|---|
| `astro-imaging-a0` | **PM.** You report to it; it signs off all work. |
| `astro-imaging-74` | Fresh worker, reading in. |
| `astro-imaging-d5` | Second worker session, holding. |

The previous worker hit 100% context and was stopped by its user **mid-unit,
holding three dirty files** — so the tree may contain uncommitted work that is not
in `git log`. **The batch is NOT closed and the release is owner-gated.**

Three things were in flight when the batch was called: `d5`'s measurement on the
cloud signature (decides whether `intake-culling` is the next batch), the worker's
rule-3 compression, and a `manifest.tsv` completeness sweep. **The PM is holding a
`TOOLS.md` pointer at `manifest.tsv` until that sweep says it is complete.**

---

## 2. THE UNCHECKED LIST — LIVE

1. **Corner ⟂ compose independence — BACK TO UNCHECKED. The upgrade to "partially
   supported" was quote-verification, not inference-testing, and one of its two
   citations no longer exists.** *Flagged by its own author against their own
   priority argument.*
   **THE CITATION IS DEAD AND THE COORDINATE WAS WRONG.** It read `BACKLOG.md:88`
   for *"the radius trend is the members' own"*. Line 88 is unrelated text, and the
   phrase is in **no tracked file except this one**. `git log -S` settles it: added
   to `BACKLOG.md` at `4a6a030`, **DELETED at `2bd3d61` (the rule-3 compression),
   and migrated nowhere** — so the compression's *"nothing reusable was lost"* has
   at least one counterexample, and an UNCHECKED entry has been resting on deleted
   text. **State the artifact-derived command, never the coordinate** — third
   instance of a wrong line number in this file's history.
   **WHAT `BACKLOG.md` ACTUALLY SAYS** (`member_separation.py` row, artifact-read):
   *"that product's delivered major axis at matched member-own radius runs
   **0.04-0.25 px above its members'**"*. **That is a MAGNITUDE. It is not the
   "no radial trend" claim the independence argument turns on** — that half rests
   on the corner-quality REPORT alone (*"a roughly radius-independent +0.04 to
   +0.28 px … and no radial trend"*), which is one record, not two.
   **AND THE INFERENCE WAS NEVER TESTED, WHICH IS THE LARGER GAP.** *"The compose
   adds an offset, not a trend"* does **not** imply the two defects are
   INDEPENDENT: a constant offset and a radial trend can share a common cause, since
   anything degrading a member's PSF also degrades what the compose resamples.
   **THE FALSIFIER, and it is runnable on the shipped instrument:** measure the
   compose's added offset **as a function of the MEMBERS' OWN corner degradation**.
   If members with worse corner terms show a larger compose offset, the two are
   coupled and independence FAILS; if the offset is flat against member corner
   quality, independence holds. `member_separation.py` already bins by member-own
   field radius and the compose delta is already measured per box.
   **Goes live the moment anyone proposes the SWarp/TPV route on priority grounds.**
2. **A fresh clone completes the astromatic build.** The bootstrap now reaches
   `install_astromatic.sh` (`x86_bootstrap.sh:511-515`); nobody has run a clone.
3. **`manifest.tsv` completeness.** Falsified once, four rows added. *"Fixed the
   four we found" is not "complete."*
4. **The 35.6's own reference distribution.** The load-bearing number of the whole
   error-model finding; untested by anyone. *[My uncertified view: a 400-resample
   bootstrap has effectively large ν, so χ² is approximately right for it — but it
   is the artifact the correction retired, so validating it may be effort spent on
   a discarded number.]*
5. **FIVE EXTERNAL CLAIMS AN ORACLE MADE WITHOUT AN EXTERNAL SOURCE — its own
   self-audit at retirement, re-homed here because a retiring session's enumeration
   otherwise dies with it.** The engagement cited **zero** external sources; every
   authority was `--help`, `readelf`, `dpkg`, `apt-cache` or this tree.
   **Capability was NOT the cause** — `WebSearch`/`WebFetch` were present and
   unblocked and the question never arose. Each of these is settled only by a source
   we do not possess:
   - **`photutils.Background2D.background_mesh` asserted from memory** as *"the
     astropy-affiliated standard exposure of exactly this quantity"* and recommended
     for the research queue. **The docs were never opened.** *Whether it yields
     fitted gradient numbers or a mesh still requiring a fit decides the
     recommendation.* **CORRECTION TO THE SELF-REPORT, artifact-checked: it did NOT
     land — `photutils` is in no tracked file** (it was in a deep-dive added at
     `a3b7ecf` and retired at `e730d3b`). **The self-audit overstated its own
     consequence, in the self-critical direction** — the reverse of the usual
     flattering-error direction, and worth noting as such.
   - **lensfun 0.3.95 / ACM** — checked against `apt` only. **Released? stable?
     shipping ACM in the correcting direction? All upstream questions, unasked.** The
     closure reads as standing on a checked negative; it stands on a checked *apt*
     negative.
   - **`lenstool`** — see the entry below; upstream may ship what Debian does not
     build, which moves *unavailable* to *one build away*.
   - **The `get_selection_stats` doc defect** — Siril's issue tracker was never
     checked for an existing report, so the owner was advised on whether to FILE
     without knowing whether it is already filed.
   - **SExtractor's background estimator** — `BACK_PEARSON 2.5` and the
     σ-clipped/object-masking account came from the config dump plus recall.
     **Bertin & Arnouts 1996 is the authority and was not read.**
   **THE STRUCTURAL CAUSE, and it is why no session was replaced over this:** the
   role file gave a detailed METHOD for the inward sweep and only an ASPIRATION for
   the outward research, and every target it was handed was locally answerable.
   **Method beats aspiration.** Fixed at `a90c315`; the aiming was the manager's
   error, not the role's.

---

## 3. SEARCHED AND EMPTY — DO NOT RE-RUN THESE

Each cost real tokens and each closed a route by being empty. **A searched negative
reported as a negative is a deliverable** (template, removal condition).

- **No installed tool reports a propagated error on a shape moment.** SExtractor's
  moments carry none and its `ERR*` families are all POSITIONAL; PSFEx gives χ² and
  per-grid min/mean/max with no error; SCAMP gives per-context residual RMS.
- **No tool fits a linear-trail model reporting length L directly.** SExtractor has
  only second moments; **TRIPPy takes `rate`, `angle`, `dt` as INPUTS**
  (`psf.py:531`) and would consume the answer as a precondition; `astride` and
  `acstools.satdet` are built for trails many PSF widths long. **The null is
  structural — the field measures sub-PSF elongation as an ellipticity and stops,
  so nobody outside this project wants a sub-PSF trail length.**
- **No packaged headless CPU Linux tool for anisotropic spatially-varying
  deconvolution.** `torchmfbd` 0.9.2 exists and is pip-installable but drags torch
  + triton onto a GPU-less rig, and **MOMFBD's premise is frame-to-frame aberration
  DIVERSITY while this corpus's aberration is static.** `sf_deconvolve` works on
  postage stamps, not fields. `properimage` **does not install** (build failure).
- **No shutter-metrology literature** using trail length to measure effective
  exposure; the trail-length relation is covered only in the forward direction
  (NPF/500-rule calculators).
- **No documented treatment of trail-profile non-uniformity** in fixed-mount
  imaging; the trail-fitting literature models constant-rate top-hats only.
- **No upstream Siril or flatpak issue** for concurrent `siril-cli` instance-dir
  collisions — and the instance dir is a **flatpak** construct, so searching
  Siril's tracker will keep returning empty whether or not the bug exists.
- **No SCAMP photometric-mode minimum-detections threshold** in its documentation;
  the 2.6.2 manual contains five occurrences of "photometr" and no photometry
  chapter.
- **`lenstool` unpackaged — UNCHECKED, by my own admission.** I used
  `apt-cache policy`, which is the instrument that produced the SCAMP error. The
  completing check is `apt-cache showsrc lenstool`. **The PM directed not to spend
  on it** — a lensfun query CLI answers no live question.

---

## 4. LOAD-BEARING FINDINGS, TAGGED — the tag does not survive summarisation

**MEASURED** — I read the artifact; all independently reproduced by the PM.

- **SWarp has no SIP reader and fails silently.** Zero `A_ORDER`/`B_ORDER`/`-SIP`
  in the 2.41.5 source. `src/wcs/wcs.c:488` matches the projection on **3
  characters** (`RA---TAN-SIP` → `TAN`); `:528` validates axis consistency on **8**
  (`DEC--TAN-SIP` passes as `DEC--TAN`), so no error; `src/fitswcs.c:842` gates
  distortion on PV terms SIP does not carry. Confirmed by SWarp itself under
  `-HEADER_ONLY Y`.
- **`sip_tpv`'s forward path contains no fit** — symbolic substitution only; the
  reverse (`fitreverse`, default order 4) is the approximate direction. *The
  exactness CONSEQUENCE was mechanism; the team then measured it end-to-end at
  1.118e-11 px max, flat in field radius.*
- **SCAMP: photometric mode is a scalar per exposure per instrument**
  (`src/preflist.h` has no photometric analogue of `DISTORT_DEGREES`); **astrometric
  side offers `PROJECTION_TYPE SAME|TPV|TAN` and defaults to `STABILITY_TYPE
  INSTRUMENT`** — the shared-context architecture.
- **SExtractor's `ERR*` families are positional, not shape-moment errors.** *I
  verified three parameters; the PM measured four full families and the claim
  stands on its measurement, not mine.*
- **No repo script can import the tool layer** — 135 bare `python3` + 40
  `env python3`, all resolving to `/usr/bin/python3`, which imports none of the six
  installed packages.
- **`pss`/`register_mpp`/`stack_mpp` are absent from Siril 1.4.4.**
- **`rmgreen`'s own help calls it "a chromatic noise reduction filter"** — which is
  why *"Siril has NO native chrominance-noise tool"* is refutable as worded.

**MECHANISM** — my derivation. **None of these is measured. Treat as hypotheses.**

- **The small-N error work.** t not z, F(1,ν) not χ², null expectation ν/(ν−2),
  variance undefined at ν=4. **The structure held; my CONSTANT (ν=4) was wrong** —
  ν is per-call and runs 3 to 39.
- **SCAMP's pooled-order argument** — 37 catalogue matches per frame supports order
  1, but `STABILITY_TYPE INSTRUMENT` pools across exposures, so ~480 across 13
  members reaches order 3–4 on the Pan-STARRS table. **Conditional on pooled
  OCCUPANCY, which nobody has checked.**
- **Gnomonic plate-scale contamination of the trail prediction** — a constant
  16.979 ″/px across a field whose local scale varies +9.6% radially / +4.7%
  tangentially, both RADIAL functions and therefore confounded with the radial
  term. **Never tested.**
- **Differential refraction is 1–2 orders below the measurement** at this pixel
  scale. Arithmetic on their header scale plus a cited dispersion figure.
- **"Pool a variance MODEL, not a value"** as the heteroscedastic small-N remedy.
- **Field-constant coma (NAT) as the explanation for the unattributed "fixed"
  term.** Never tested.
- **"A claim corrected at its reporting site survives everywhere else it lives."**
  One confirmed instance — mine. **The PM swept its own corrections and found no
  siblings, so the mechanism is real and the RATE is unknown.**

**DOCTRINE** — external literature, cited, not measured here: Pan-STARRS Table 5
(arXiv:1612.05244) for star-count-vs-polynomial-order; Andrae, Schulze-Hartung &
Melchior (arXiv:1012.3754) for reduced-χ² at small N; Nodal Aberration Theory
(Thompson 2005; Schechter & Levinson arXiv:1009.0708) including **binodal
astigmatism as a coma/astigmatism discriminator at a single focus**; Zackay & Ofek
(arXiv:1512.06872/06879) — **PSF homogenisation loses sensitivity**, which is why
the owner's refusal is formally backed; Veres et al. 2012 for Gaussian-fit-to-trail
bounds (10–20%); IMCOM (Rowe, Hirata & Rhodes; `pyimcom` on PyPI, coupled to named
input readers, adapter cost is weeks and a fork).

---

## 5. TWO ROUTES THAT ARE OPEN AND WHAT GATES THEM

**SWarp/TPV on `compose-homography-smear`** — the largest measured defect. `sip_tpv`
verified exact; SWarp confirmed SIP-blind; SCAMP is the native TPV producer.
**Gated on:** the `$ASTRO_VENV` consumer wiring (§4, no script can import the tool
layer — follow `solve_field.py:94-116`'s re-exec pattern), and on unchecked premise
#1 if it is argued on priority grounds.

**`intake-culling`** — user-directed, foundational. **2 rows done, 1 blocker stale
(cloud — `bg` per frame IS recorded), 4 open.** If `d5`'s measurement kills the
cloud signature, the fallback is the light-pollution/moon row needing **background
gradient magnitude + bearing**, which `records.jsonl` does not carry — **a bigger
unit, not a smaller one.** A kill there is the item's own rule firing on itself
(*a signature that cannot be made to fail on demand is decoration*), so report it
as a result rather than a setback.
