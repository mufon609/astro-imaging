# Prompt for a fresh session — the sky-flat gradient. Paste everything below this line

---

There is a measured defect in this pipeline. Your job is to characterise it
properly and find the fix — under strict rules, because the last thing this repo
needs is another confident change that was never tested.

**READ FIRST, in this order:** `CLAUDE.md` → `docs/dead-ends.md` → `TOOLS.md` →
`MEMORY.md` → `README.md` → `BACKLOG.md` → `datasets/README.md`.
Then `datasets/july31/flat_gradient_measurement.json`, which is the measurement
this prompt is built on.

## The defect, as measured

Each of july31's four sets was calibrated with its **own** sky flat, built from
that set's own lights. Dividing one flat by another **cancels the optical
response exactly** — same lens, same focal, same aperture, same focus, same
night — so the ratio isolates whatever else is in them. A flat is `V × (1+g)`:
optical response times whatever sky was baked in. `flat_i / flat_j` = `(1+g_i)/(1+g_j)`,
with no model, no fit, and no assumption.

Measured with Siril alone (`idiv`, then `crop` + `stat` medians):

| ratio | corner spread |
|---|---|
| flat01 / flat02 | 7.11% |
| flat02 / flat03 | 10.56% |
| flat03 / flat04 | 12.07% |
| flat01 / flat03 | 18.55% |
| flat01 / flat04 | **31.68%** |

Adjacent gaps sum to the wide gaps (7.11+10.56 = 17.67 vs 18.55 measured;
+12.07 = 29.74 vs 31.68). A 5×5 grid on flat01/flat03 shows a smooth monotonic
diagonal tilt, −8.05% to +9.70%, **19.31% peak-to-peak**, with no structure
beyond the tilt at that sampling.

So: **the flats disagree with each other by up to 31%, and the disagreement grows
monotonically through the night.** Since `V` cancels, that is sky, not optics.

Images to look at first: `web/results/july31/flat_gradient/flatratio_set-01_over_set-03.png`
and `..._over_set-04.png` — autostretched, so read them as shape, never as
magnitude (`docs/dead-ends.md` records the judge stretch amplifying a background
gradient 9–17×).

## What is NOT the problem, and why — do not re-litigate these

- **Vignetting, or any optical/lens term.** Cancels by construction in a ratio of
  two flats from the same optics on the same night. That is precisely why the
  ratio was used instead of comparing a flat against a model. The pinned lens
  distortion model was identical for all four sets and asserted per set.
- **Frame count.** `flat02/flat03` is 500 frames against 500 — *identical* — and
  still shows 10.56%. set-04 having fewer frames (260) cannot produce a trend that
  is already present between two equal-count sets.
- **Dew.** Its recorded signature (july23, `docs/dead-ends.md`) is a growing star
  halo with rising FWHM **and a terminal nstars crash of 13–16%**. Here nstars
  *rises* through the night (1166 → 1256, +8%) while FWHM creeps 2.334 → 2.576 px.
  A rising star count is the opposite of dew.
- **The sky getting brighter.** Background level is flat across all four sets
  (bg16 median 1117 / 1115 / 1117 / 1117). The sky did not brighten — its gradient
  changed *direction and magnitude*. That is a geometry change, not a brightness
  change, which is what makes it interesting.
- **Seeing / focus drift.** FWHM creeps ~10% but that is a star-shape term. It
  cannot produce a smooth 31% diagonal tilt in a median of 500 frames.

## What IS the likely source — and the distinction that matters

july31 was shot under a **93.7% moon**. Moonlight plus airmass produces a bright
gradient that is fixed relative to the **horizon**. On a fixed mount the camera is
horizon-fixed too, so that gradient sits *still on the sensor* while the sky drifts
past — and therefore **cannot reject out of a median of un-registered lights**. It
integrates straight into the flat. As the night progresses the moon moves and the
airmass geometry rotates, so each set bakes in a *different* gradient. That is the
documented mechanism in `docs/dead-ends.md`.

**The moon is the SOURCE of the gradient. It is not the defect.** No processing
removes moonlight, and telling the user to avoid the moon is not an answer — this
repo must handle data as captured. The defect is that a flat built from those same
lights *absorbs* the gradient, and division then stamps its **inverse onto the
object**: lights are `(sky+object)×V`, the flat is `V×(1+g)`, so calibration yields
`(sky+object)/(1+g)` — the sky's own gradient does come out, and the object is left
carrying a multiplicative tilt it never had.

## The consequence — HYPOTHESIS, not established

Each set's object is modulated by `1/(1+g_i)` with a *different* `g_i`. Registered
to sky and combined, four different multiplicative tilts do not cancel; they leave
a residual that is neither sky nor object.

Two observations consistent with this, neither yet tested as such:

1. **Linear corner spread rises in capture order** across the per-set stacks:
   0.40 / 0.50 / 1.03 / 1.17 % (sets 01–04, Siril `stat`, box 400 / margin 200,
   linear `_spcc` stacks). Frame count does not explain a monotonic trend in
   capture order.
2. **The user reports the combined frame looking duller than expected toward the
   top-right of the North America Nebula.** NGC 7000 sits at pixel (2339, 612) in
   `stack_all4_full_wcs.fit`'s FITS convention. This has NOT been measured — treat
   it as the user's visual report and establish it with an instrument before
   building anything on it.

There is also a **second, distinct mechanism from the same root** that you must
separate from the tilt: a sky flat is a median of un-registered lights, so any
structure that does not drift far enough relative to its own size **bakes into the
flat and is then attenuated by division**. That suppresses the object *locally*,
where a tilt suppresses it *smoothly*. Local dullness near a large nebula is more
consistent with baking than with tilt. These predict different spatial signatures
and must not be conflated.

## Rules — binding, and the reason for each

1. **Do NOT alter the pipeline or the documentation until a controlled test has
   confirmed the cause.** Not the scripts, not the registry, not the recipes. The
   measurement above establishes that the flats *differ*; it does not establish
   what that does to a deliverable. Write the fix only after the test says what
   the fix is.
2. **The baseline stays exactly as it is** unless an issue is correctly
   identified. The four `_full` stacks and the combined stack are user-accepted.
   They are the control. Do not rebuild over them, do not re-seed a baseline, do
   not "improve" anything in passing.
3. **One variable per run.** Change the flat, change nothing else — same frames,
   same dark, same cull, same route, same group size, same rejection, same model.
   State the knob and the control before you run.
4. **Never conclude from metrics alone — RUN THE PIPELINE.** A difference between
   two flats is not a difference between two deliverables. If you claim the flat
   changes the product, you must produce both products and measure them.
   Pre-register the instrument and the threshold *before* the run, and use the
   repo's own floors: the compose-repeat floor is 0.00 px (bit-identical, n=2);
   there is still **no rebuild-repeat floor**, so if your effect is small, measure
   that floor first or your number means nothing.
5. **Official tools only.** Siril, darktable, ASTAP, astrometry.net, GraXpert,
   Hugin — every pixel operation and every standard measurement. In-house code
   orchestrates and records; it does not analyse the deliverable's pixels.
   *Peeking at data to understand it is fine* — read a header, plot something for
   yourself, look at numbers. The line is that anything entering a conclusion or
   the pipeline comes from a tool. Note that `idiv` on two flats is the whole
   instrument here; you rarely need more than Siril's own arithmetic.
6. **Research before building.** This is a known problem class in the field —
   gradient extraction, flat sources, moonlit-sky calibration. Read the primary
   sources (Siril docs, PixInsight doctrine, the tools' own documentation) before
   proposing a mechanism, and cite what you find. `TOOLS.md` is the toolkit and
   should be updated from primary sources when you learn something durable.

## What a good answer looks like

- The two mechanisms (smooth tilt vs local baking) **separated by their measured
  spatial signatures**, not by argument.
- The user's dull-region report either **confirmed or refuted with an instrument**,
  in the linear domain, never off the stretched PNG.
- A candidate fix that is a **route through an official tool**, tested one-knob
  against the accepted baseline, with the product measured — not a plausible
  mechanism with a metric attached.
- A clean NULL is a real result. So is "the flats differ by 31% and it does not
  measurably reach the deliverable" — that would be worth knowing and would close
  the item.

## What is on disk

Raw frames only, plus the objects under investigation and the accepted baseline:

- `sessions/july31/{darks,set-01..04}/` — 2114 raw NEF, the whole session
- `sessions/july31/work/masters/` — the master dark and the four per-set sky flats
- `web/results/july31/stack_set-0{1..4}_full{,_spcc}.fit` — the accepted per-set stacks
- `web/results/july31/stack_all4_full{,_spcc}.fit` — the accepted 1760-frame combine
- `web/results/july31/judge/*.png` — the five accepted judge surfaces
- `web/results/july31/flat_gradient/` — the flat-ratio diagnostics above

Everything else was removed as superseded and is regenerable from the raws. The
route experiments' conclusions live in `datasets/july31/experiments.jsonl` with
their numbers.
