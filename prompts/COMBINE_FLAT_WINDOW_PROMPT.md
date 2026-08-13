# Fresh-session brief — the flat window at the COMBINE unit

**SELF-RETIRING.** Delete this file in the commit that lands the verdict.

**STAGED, NOT CLEARED TO RUN.** The owner staged this item; before starting,
confirm with them that the machine is free — this is a multi-set member rebuild
and the L1 build has prior claim. Read `BACKLOG:per-group-flat-at-the-combine`
first; it carries the numbers and this brief does not restate them.

**Scope note on the pause.** The flat-residual line is paused pending real flats.
That pause is about measuring the ABSOLUTE magnitude of the `sky × V` defect,
which needs a reference this repo does not have. **This item is a different
question** — a route choice between two synthetic-flat policies, both already
shipped-builder products — and the owner staged it explicitly. Do not read the
pause as covering it, and do not drift from this question into that one.

## What is settled, and what is not

Settled at the per-set deliverable: per-group flats are a **NULL** there.
Composed object tilt +0.055% ± 0.083%, 0.7σ over 1217 stars — zero *by
construction*, because the set flat already IS the mean of the group flats, so a
plain-mean compose cannot tell them apart.

Not settled, and the reason this item exists: what per-group flats actually
change is the **member** — 1:1 transfer, object tilt moving 0.36–2.13% in x at
4.3–21.3σ, backgrounds 28–40× more consistent member-to-member (recorded as the
mechanism's SIZE, never as evidence of better calibration — that is the
self-fulfilling direction), against a **cost** of 3.271% (x) / 4.335% (y)
member-to-member object-imprint disagreement where the shipped route has exactly
zero.

**The member is the cross-night COMBINE unit.** MEMORY's rule is that a
calibration/route change is evaluated against the combine, not just per-set
products. So the trade's sign is untested where it matters most.

## The question, stated so it cannot drift

Per-SET flats give every member of a set one shared imprint: uniform within a
set, differing across sets and nights. Per-GROUP flats add within-set variation
on top of that. At a cross-night combine, does the member-to-member disagreement
**average away** — because across-night flat differences already dominate it — or
**compound**?

**Both outcomes are live and neither is the expected one.** The cancellation
argument says within-set variation is second-order against a corpus whose flats
sweep +0.436 → −0.385 in edge dipole. The compounding argument says per-group
flats reduce each member's own error, so the across-set spread could shrink even
as within-set spread grows. Pre-register which you expect, with a mechanism, and
a falsifier for each.

## Scoping — verified on disk, and it is the expensive part

- **Arm A (control) exists in full.** The whole 12-set corpus is built with
  per-set flats, and `web/results/aug06/stack_set-01+02+03_full*.fit` and the
  night/corpus unions are on disk.
- **Arm B barely exists.** Only july31/set-03 has per-group flats
  (`sessions/july31/work/masters/pergroup/`), and **no set has arm-B members
  built** — verified. Everything else is a build.

So the cost is: per-group flats plus a full member rebuild for every set entering
the test combine. **Choose the combine unit deliberately and state why**, because
it decides the bill:

- **A cross-night pair is the minimum that answers the question** — the whole
  point is different skies, and a within-night combine cannot see it.
- A night-level combine is cheaper and answers a **different, lesser** question.
  If you run it, say so; do not let it stand in for the cross-night answer.
- The full corpus answers it best and costs the most. Time is not the constraint
  the owner cares about; **being wrong is** — but scope creep that never finishes
  is also a failure.

## Carry these forward — they are measured, not advice

- **Registration must be pinned across arms.** Changing the calibration changes
  `register -2pass`'s reference (measured twice now: 4896×3616 vs 4887×3641 from
  a flat change; reference 8 → 11 from `--subsky-lights`). `--regdata-dir=` and
  `--tag=` are plumbed through `run_undistort_groups.sh`; use them.
- **`-nonorm` for the pixel instrument, plus one production-normalized pair.**
  The shipped normalization absorbs ~0.3% on the object but moves the background
  field ~48.6%.
- **The imprint rule is about what the flat DESCRIBES**, not optical state: it
  fires when a flat averages frames that saw DIFFERENT skies, so it describes a
  blend no frame saw. Under one continuous pointing there is no blend. Do not
  re-derive this, and do not re-argue the doctrinal case for per-group flats — it
  was refuted.
- **Never judge on stack corner spread**; corner-vs-centre is self-fulfilling for
  flat contamination. Use the differential instrument and the grid-fitted ramp.
- **Do not run `install_lens_model.sh` while a build is in flight** — it rewrites
  the global lensfun DB the live warp is reading.
- **A fixture for a RATIO must divide by what the code divides by**, not by what
  the fixture happens to know. Both sessions got this wrong on the L1 instrument.

## Acceptance

The house pattern applies in full: prediction committed BEFORE any arm exists;
falsifiers named and evaluated by name; a floor control and a planted control
with the discrimination reported; a selftest that falsifies its own mechanism in
process; every number with its instrument, n and the box's `uptime`; guards and
selftests green; `prompts/REPORT.md` updated and this file deleted in the same
commit. If a peer session is live, apply the parallel-session rules in
`CLAUDE.md` — count the diff before committing any file, and name the file you
committed.

## Honest failure

A NULL here is a real outcome and the more likely one on the cancellation
argument. Report it as what it is — the member-level trade does not reach the
combine — not as "no difference". And if the answer is that it compounds, that
does not by itself adopt per-group flats: the trade still has no measurable
"better", so the choice stays the owner's under the evidence gate.

Verify everything in this brief against the repo before relying on it.
