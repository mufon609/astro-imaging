# Fresh-session prompt — the domain-corrected iterative sky flat

**Do not take this document's word for anything** — verify every claim in the
repo before acting on it. Read `CLAUDE.md`, then `docs/dead-ends.md` COMPLETELY
(this experiment lives in the registry's most trap-dense territory; the 31×
regression it must not repeat is documented there with its full mechanism),
then `BACKLOG.md` `calibration-evidence`, then `scripts/stack/build_sky_flat.sh`
top to bottom, then `git log` for the desky arc.

**This is an EXPERIMENT, not a fix-on-order.** One knob, hypothesis
pre-registered before any run, judged on the instruments named below, closed
WIN or clean NULL into `datasets/aug09/experiments.jsonl` — and a kill goes to
`docs/dead-ends.md` with its numbers. Nothing here touches a shipped product;
adoption is a separate, owner-ratified step after the verdict.

---

## The defect, measured — and the part that must NOT be "fixed"

A sky flat is built from the set's own lights, so it converges to
`(mean sky) × V`: any sky-brightness structure fixed relative to the HORIZON
cannot drift out (the camera is horizon-fixed too), bakes into the flat, and
division then tilts the OBJECT by a multiplicative gradient it never had
(recorded at 3.11% / 241σ by differential star photometry — a figure with NO
tracked record; `BACKLOG:calibration-evidence` carries the re-measurement
design). New evidence, the sharpest yet: aug09's five flats form a MONOTONIC
DOSE CURVE — corner-asymmetry ratio **1.127 → 1.211 → 1.317 → 1.403 → 1.468**
in time order, same orientation every set (brightest BL, darkest TR), tracking
that night's independently measured haze thickening (+8% sky rise through the
night, +0.16 mag extinction, 16,913 matched stars). Records:
`datasets/aug09/set-0*/qa_work/skyflat_*_qa.json`.

**Decompose before you build anything.** The curve has two components and only
one is the enemy:

- the GROWING term (1.127 → 1.468) is the baked sky gradient — the target;
- the STABLE BASE (~1.13, matching july23/july27's 1.126–1.33 family across
  nights) contains a real instrumental odd component that is a CORRECT
  correction: july31's flat edge-dipole X (+0.365…+0.43) has the SAME SIGN as
  the raw dark-subtracted light's own asymmetry (+0.426) — the flat is
  correcting real optics there. A "fix" that zeroes the whole odd component
  UNDOES that correction; the registered `--desky` regression's defining
  signature was exactly this term driven through zero to −0.550.

Cheap first measurement (do it before designing anything): ratio pairs of
aug09 flats via `fdiv <B> 0.5` (NEVER `idiv` — it clips at 1.0 silently;
record the scalar; two scalars agreeing after rescale is the no-clip control)
— set-05/set-01 isolates the pure sky-dose term with the instrumental base and
vignetting cancelled exactly (same lens/night/builder).

## The dead-end fence — read each entry in `docs/dead-ends.md` before running

1. **`--desky` (seqsubsky on the flat's RAW source frames): DEAD, 31×
   regression** (corner spread 12.4% vs 0.4%; edge sign INVERTED +0.426 →
   −0.550). Mechanism: background extraction is defined on FLAT-FIELDED data;
   raw frames are `sky × V`, and the plane fit overshoots where V curves
   hardest. This prompt's scheme runs the operator in the CORRECT domain —
   do not re-run the raw-domain form, and do not cite its failure against the
   corrected-domain form (the registry entry itself draws that split).
2. **Degree ≥ 2 backgrounds: parity-blocked** on un-flat-fielded frames
   (erased the vignetting profile outright, corner/centre 0.51→0.94+), and on
   flat-fielded frames degree ≥ 2 eats the frame-filling UNRESOLVED STARLIGHT
   (it is STARS — R² 0.9631 vs Gaia; terminology entry). **Degree 1 only,
   everywhere in this experiment.**
3. **`seqsubsky` dithers by DEFAULT and the dither is UNSEEDED** — `-nodither`
   is mandatory (measured ±0.4 ADU run-to-run without it; bit-identical with).
4. **The whole-frame odd-PLANE fit is a LIAR here**: it CANCELS under a
   partial sign inversion — the shipped `--desky` validated green on it while
   regressing 31×. Success is judged on EDGE dipoles (box 80 / margin 2, the
   `baseline_guard` geometry), the corner ratio, and the SIGN-vs-raw-light
   check — never on a whole-frame plane fit.
5. **GraXpert `-correction Division`**: absorbs ~2/3 of extended structure on
   MW-filled fields — not a comparator, not a fallback here.
6. **A stack-level A/B resolves nothing below the run-to-run floor** (2.06%
   star edges / 0.073% flat sky) — judge the FLAT on the flat's own records;
   judge downstream on linear regional numbers and like-encoded surfaces.
7. Flats and lights are 32-bit everywhere (`set32bits` pinned; the guard
   enforces); `.ssf` files live under `$HOME` (flatpak's /tmp is private);
   record `uptime` with any instrument reading; `pgrep` the chain scripts
   before editing any of them.

## The scheme under test (verify the algebra before implementing)

Pass 1 is today's builder unchanged: `F0` from CFA, dark-subtracted,
un-registered lights, `-norm=mul`, winsorized. Then:

1. calibrate the same CFA lights with the master dark AND `-flat=F0` — the
   frames are now FLAT-FIELDED: the operator's correct domain, `≈ (S+O)/S̄`;
2. `seqsubsky 1 -nodither` on those frames — removes each frame's additive
   sky PLANE (tilt and level);
3. **restore each frame's own sky LEVEL as a constant** (Siril `offset` with
   that frame's pre-subsky background median, read from Siril's own `stat` —
   the level is what the flat stack needs for signal; only the TILT must die);
4. return to the sensor domain by multiplying back by `F0` (Siril `imul`) —
   each frame is now `≈ (S̄_t + O) × V`: a GRADIENT-FREE sky times the true
   vignetting;
5. rebuild the flat from these frames with the SAME stack recipe → `F1`.

**Verify the algebra symbolically first, then on a synthetic fixture where
truth is known** (a card = known even vignetting × known odd gradient,
composable with Siril arithmetic; the fixture-discipline entry applies — prove
the fixture exercises the live path, and prove the recovery fails when the
mechanism is deliberately broken). Only then touch real frames. One iteration
is the hypothesis (the residual after one pass is second-order in a ≤20%
gradient); a second pass needs its own measured justification, cap at two.

Implementation: a flag on `build_sky_flat.sh` (default OFF; the chain does not
pass it until adoption is ratified), emitting the same records plus the
iteration's own before/after numbers. New `.ssf` emissions carry the standard
pins; run the guards after editing.

## Acceptance — measured, in this order

1. **Synthetic fixture:** recovers the known V with the known gradient
   removed; breaking the mechanism (skip step 3, or degree 2 in step 2) makes
   it fail visibly — executed, not argued.
2. **The dose curve collapses:** rebuild all five aug09 flats with the
   corrected builder — corner ratios must fall TOWARD the stable base
   (~1.13 family) with the monotonic growth gone; sets 04/05 (1.403/1.468)
   are the strongest tests.
3. **The correct correction survives:** july31/set-01's flat rebuilt the same
   way must keep its edge-dipole X SAME-SIGN as the raw light (+0.4-family,
   never inverted) and its vignetting profile (corners < centre, ratio in
   family — corners going to ~1.0 is the degree-2 kill signature).
4. **Starlight survives:** the builder's own speck gate, and no smoothing or
   absorption of the frame-filling starlight (degree 1 only is the guard).
5. **Downstream, one knob:** ONE aug09 set's stack rebuilt with F1 against
   the shipped F0 stack (tagged output — never overwrite the shipped
   product): linear corner spread + edge dipoles + like-encoded judge
   surfaces at 1:1. Declared delta; anything aesthetic is the owner's eyes.
6. **The original wound, if the arm is affordable:** the catalogue-free
   object-tilt test pre-designed in `BACKLOG:calibration-evidence` (first
   third vs last third of a set, same stars at different sensor positions —
   flux must not depend on where a star landed). A fix should SHRINK the
   tilt; measuring it also finally gives the 3.11%/241σ claim a tracked
   record. If deferred, say so explicitly.
7. Ledger entries closed WIN | NULL; a kill lands in `docs/dead-ends.md` with
   numbers; the new divergence gets its removal-conditions row IN THE SAME
   COMMIT (retires when a matching real flat exists for the set, or the
   gradient class is measured absent); the WARN threshold (1.20, provisional)
   is NOT tuned as part of this work — loosening an acceptance measure needs
   explicit owner ratification and is not the fix.

## Rules

- Official tools do every pixel operation and measurement — the iteration is
  ORCHESTRATION of Siril ops (`calibrate`, `seqsubsky 1 -nodither`, `offset`,
  `imul`, `stack`); no numpy touches any frame.
- One knob per experiment; hypothesis pre-registered in the ledger BEFORE the
  first real-data run.
- Comments: load-bearing constraint + numbers, present tense, nothing that
  ages; no chronology.
- Do not `git push` unless asked. Do not delete raw frames. Do not overwrite
  any shipped product. Retire this prompt (`git rm`) when the verdict is
  recorded — WIN or NULL, the registry and ledger carry it either way.

## Deliverable

A cited `.md` at the repo root: the decomposition numbers, the verified
algebra, the fixture proof (including its deliberate failure), the five-flat
dose-curve table before/after, the sign/vignetting survival numbers, the
downstream delta with surfaces for the owner's eyes, and the ledger/registry
entries. If the scheme fails, the most valuable outcome is the same as ever:
the numbers, the mechanism, and a dead-ends entry that keeps anyone from
walking this ground twice.
