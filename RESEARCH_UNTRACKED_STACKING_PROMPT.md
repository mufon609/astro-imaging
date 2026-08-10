# Fresh-session research prompt — how the field actually stacks UNTRACKED camera-lens wide-field

**Read this and nothing else first.** You are being asked deliberately as a fresh
set of eyes. Do **not** read `CLAUDE.md`, `docs/`, `BACKLOG.md` or any prior report
in this repo before you have formed your own answer from primary sources — the
point of this task is an unanchored reading of what the tools and the field
recommend. Once you have written your findings you may read the repo to note where
it agrees or differs, and that comparison goes in a clearly separated section at the
end.

This is a **RESEARCH** task. No processing, no experiments, no pixel work.

---

## The setup, stated neutrally

- Camera: Nikon Z6 III, **NIKKOR Z 24-70mm f/4 S at 70 mm, f/4**, manual focus at
  infinity, focus verified correct.
- Mount: **fixed photo tripod, no tracking, no dithering**. Alt-az fixed, so the
  sky drifts across the sensor and the field also rotates slowly.
- Frames: 2.5 s, ISO 1600, ~500 per set at a 3.00 s interval — a continuous
  ~25-minute run per set. Several sets per night, re-aimed between sets, and
  several nights combined.
- Sensor 6064x4040, plate scale ~17.06 arcsec/px, field 28.6 deg.
- Target near the galactic plane at Dec ~+42, observed at 72-77 deg altitude.
- Linux, headless, CPU-only. Siril 1.4.4 is the workhorse. darktable 5.4.1 +
  lensfun 0.3.4 are available. PixInsight is NOT installed and is a paid tool —
  we still want to know what it does, because knowing the standard matters even
  where we cannot run it.

## The measured symptom

Every number below is a tool's (Siril `findstar` on stacked results, Siril's own
registration homographies, astrometry.net solves). They are stated so you can judge
them; you are not being asked to accept anyone's interpretation of them.

1. Stacked results are **soft and elongated on ONE SIDE of the sensor** and clean on
   the other. At matched distance from the sensor centre, one side reads **FWHM 2.86
   px / roundness 0.821** where the opposite side reads **2.59 / 0.853**. The centre
   is fine (2.26-2.35 px, roundness 0.92-0.95).
2. The bad side is the side stars **drift OUT of**. Siril's own homographies give a
   drift of **3.87 px/frame** across the sensor; stars enter one edge and leave the
   other, and it is the exit edge that smears.
3. The effect tracks **sensor position**, not elapsed time: fitting the same 25
   measurements gives R² 0.90 against sensor x and **R² 0.05 against time**.
4. Acquisition is clean: exposure, ISO, aperture and focal length are identical
   across all 500 frames, the interval is 3.00 s with no gap anywhere, and
   differential refraction across the field changes only 0.09 px over the run.
5. In-exposure trailing is a floor here (~1.5 px at 2.5 s), so stars are never
   round; success is defined as the EDGES matching the CENTRE, not as round stars.

## The questions — answer from primary sources, with citations

**A. What does Siril itself recommend for this class?** Its own documentation,
release notes, tutorials and the free-astro forum. Specifically:
- Is there a documented Siril workflow for untracked / fixed-tripod wide-field DSLR
  or mirrorless stacking? What does it say about drift, field rotation, and how much
  sky movement one registration can absorb?
- What registration methods does 1.4/1.5 offer for this case, what transform classes
  (shift / similarity / affine / homography), and what do the docs say about when a
  global transform stops being sufficient?
- `register -disto=` / distortion handling: what is it FOR, what does it consume,
  and what does Siril say about applying a distortion solution across a sequence?
- Does Siril recommend splitting a long untracked run into shorter registration
  units, and if so on what criterion?
- Anything on choosing the registration REFERENCE frame, and whether the choice
  matters for a drifting sequence.

**B. How does PixInsight handle it?** StarAlignment's distortion correction,
thin-plate splines / local distortion, DynamicDistortionCorrection, the
"distortion model" workflow, and whatever the current recommended practice is for
wide-field camera-lens data. What does it model that a purely radial lens profile
does not?

**C. What do the astronomical standards do?** SWarp / SCAMP (Astromatic), and the
survey lineage (SDSS, CFHTLS, DES, Pan-STARRS). How is optical distortion
represented (SIP, TPV, TNX), is it derived per exposure or shared, and how is
asymmetric / decentring distortion handled?

**D. The specific technical question.** Lens-correction profiles in lensfun (and
Adobe/PTLens-style profiles generally) model distortion as a purely RADIAL function
of image radius. Real lenses also have DECENTRING (tangential) distortion —
Brown-Conrady p1, p2 — which is left-right asymmetric.
- Is a radial-only model considered adequate for astrometric-grade work, and where
  does the literature say it breaks down?
- Which tools available on Linux, free, headless can fit or apply a distortion model
  WITH tangential/decentring terms? (Consider at least: OpenCV calibration,
  Hugin/panotools, astrometry.net SIP, SCAMP, ASTAP, GraXpert, Siril itself.)
- Is there a documented way to feed such a model into Siril or into a stacking
  workflow?

**E. Is this a known problem?** Search astrophotography forums (Cloudy Nights,
free-astro, StargazersLounge, r/astrophotography), the Siril issue tracker, and
lensfun's own issue tracker for reports of one-sided / asymmetric softness in
untracked wide-field stacking with camera lenses. We specifically want to know
whether this is a commonly reported phenomenon with a known name and known
remedies, or whether it is unusual. **Report honestly if you find nothing** — a
clean negative is a useful result and must not be padded.

## Two hypotheses we hold, stated so you can ignore them

Deliberately listed LAST, and you should form your own view before weighing them:

1. An uncorrected asymmetric (decentring) distortion term, fixed in sensor
   coordinates, which a radial-only lens profile cannot remove by construction.
2. A registration failure concentrated at the exit edge: stars there are transient
   — present in fewer frames of a stack and absent from the last ones — so a global
   homography is least constrained on that side.

If the sources point somewhere neither of us has considered, say so plainly.

## What to deliver

A cited `.md` at the repo root. State for every finding whether it is
**DOCUMENTED** (a tool's own docs or a primary source), **COMMUNITY** (forum
consensus, with how many independent reports), or **INFERRED** (your reasoning).
Prefer primary and recent (2025-2026) sources, link everything, and where sources
disagree say so rather than picking one.

End with: the single change you would make to a headless Linux untracked
wide-field stacking pipeline first, and why — and what it would cost.
