# Fresh-session prompt — verify the fix holds, and prove the pipeline reproduces it

**Your job is not to take this document's word for anything.** The claims below
are what the previous session believes it measured. Your job is to rebuild the
corpus with the current chain and find out whether that survives contact with a
clean run — and to audit, harden and clean up the process while you do.

Read `CLAUDE.md` first; it is the briefing and the read order. Then `git log`.

---

## The issue, stated so you can attack it

The deliverable is a cross-night stack of untracked wide-field camera-lens data:
Nikon Z6III, NIKKOR Z 24-70/4 S at 70 mm f/4, 2.5 s subs at ISO 1600, fixed
tripod, ~28.6 degree field, three nights (july31, aug06, aug09), 5,863 light
frames in 13 sets.

**The defect.** The combined cross-night stack was smeared across roughly a fifth
of the frame — stars drawn into coherent dashes over brushed texture — while the
rest was clean. At sky position **RA 294.86, Dec +44.99** the union measured
**FWHM 4.383 px / roundness 0.458**, against **2.448 / 0.968** at a clean control
position (RA 314.72, Dec +42.15).

**The cause.** The compose aligned each member (a 100-125 frame sub-stack) to a
common reference with ONE star-pair homography, via siril `register -2pass`. The
members' optical axes span ~13 degrees of RA across two nights, and a single
projective fit cannot carry that. The information needed was already present —
the members' own astrometric solutions place the same stars within 0.10 px
median — and the homography discarded it.

**The fix.** Register the compose astrometrically: `seqplatesolve` derives the
transform from each member's OWN plate solution, and `seqapplyreg` applies that
member's OWN SIP undistortion before projecting. One knob, everything else
identical. Measured:

| position | star-pair | astrometric |
|---|---|---|
| defect RA 294.86 | 4.383 / **0.458** | 2.678 / **0.974** |
| mid RA 301.58 | 3.060 / 0.725 | 2.595 / 0.917 |
| mid RA 308.20 | 2.498 / 0.931 | 2.453 / 0.946 |
| control RA 314.72 | 2.448 / 0.968 | 2.435 / 0.961 |

The defect zone reaches the clean band's own level; the clean band does not
regress; star counts stay within 1-2% so it is not survivorship. The astrometric
canvas also covers MORE sky (800.1 against 773.5 sq.deg) in a tighter box, and
lands north-up instead of inheriting the pinned member's arbitrary orientation.

**None of that has been reproduced from raws.** It was measured on members built
by the old chain. That is what you are here to settle.

---

## Step 1 — examine the history before you run anything

`git log` is the record; the working tree is a snapshot. Recent work you should
understand before trusting or changing it:

- the astrometric compose and its two-part guard (`compose_preflight.py` plus a
  post-assert on siril's own log lines)
- the provenance stamp: composites now state their own identity instead of
  inheriting the reference member's, and every product records `REGMODEL` /
  `REGUNDIS`
- `scripts/lib/frame_order.py` — the camera's frame counter wraps at 9999, and
  filename sort is then the wrong order
- the night combine and `run_corpus_combine.sh`, which did not exist until the
  last commits and have **never been run end to end**

`docs/dead-ends.md` holds the mechanism entries and the traps. Several are
recent and none of the recent ones have been independently re-tested.

---

## Step 2 — rebuild, and render at every level

Everything is built from `sessions/<night>/<set>/` raws. Products are gitignored
and were deliberately cleared, except one kept reference (below).

**Per set** — each of the 13 sets gets its own complete render.
**Per night** — each night gets ONE combined stack of all its sets, rendered as
a full wide canvas like the approved one.
**All nights** — one final combined stack of every night, rendered the same way.

The owner's instruction for the final combine is **all images, not culled**. Note
the tension and resolve it deliberately rather than silently: the chain has a
standing auto-cull that excludes frames flagged on the tools' own registration
data (robust z >= 3.5), and a hand-ratified recipe block overrides it. Decide
whether "not culled" means *no frame excluded* or *no set excluded*, say which
you chose and why, and record it.

Entry points (read their headers — they explain themselves):

    scripts/stack/run_session_chain.sh sessions/<night> --yes
    scripts/stack/run_corpus_combine.sh sessions/july31 sessions/aug06 sessions/aug09

The set chain stops at a readiness report unless `--yes` is passed. That is the
one-approval gate, not a bug. If a gate fires, resolve the cause — do not force
past it.

---

## Step 3 — the acceptance test, and it must be measured

A render is not verified because it looks finished. For every combined product,
measure star shape at the same sky positions with the same instrument:

- Siril `findstar` with `setfindstar reset -roundness=0.10 -relax=on -maxR=1.0`
- 800 px boxes placed by the product's OWN solved WCS at RA 294.86 / Dec +44.99
  (the defect) and RA 314.72 / Dec +42.15 (the control)
- FWHM = median of (FWHMx+FWHMy)/2, roundness = median of min/max, over the 30
  brightest fits
- report `n` alongside every shape number — a shape metric without its star
  count is how survivorship bias gets mistaken for a win

**Passing means:** the defect position reads at or near the clean band
(roundness ~0.95+), the control does not regress, and star counts are comparable.
Also confirm `REGMODEL=astrometric` and `REGUNDIS=T` in the product header — if a
combine silently fell back to star-pair, the header says so.

Then look at the renders. Full-frame 16-bit PNG in `web/results/<night>/judge/`,
opened in your own viewer, at 1:1 on the defect region. A statistic can hide what
an eye catches immediately.

Kept for comparison: `web/results/aug06/stack_j31-3+a06-3_full_onemodel.fit` and
its two judge surfaces — the OLD union carrying the live defect at 0.458. It is
the number to beat. Do not delete it until the rebuild's own union is measured.

---

## Step 4 — audit, harden, clean, document

Standing work, not an afterthought:

- **Audit** what you run. If a script's header claims something, check it. The
  last session found a silent FITS truncation, a no-op deconvolution default, a
  sequence command that reported success and wrote nothing, and a builder that
  ordered frames by filename — all in code that read as correct.
- **Harden** what you find. A guard that has never fired has never been tested;
  make it fire on purpose.
- **Clean.** Remove stale root-level documents, dead scratch and superseded
  records. The convention is: findings graduate into `TOOLS.md` /
  `docs/dead-ends.md` / `BACKLOG.md`, the working document is retired, and
  recovery is by commit. **This prompt is one of those documents — retire it when
  it is answered.**
- **Document.** Update in place; no chronological narrative in records.
  `BACKLOG.md` carries the open queue and the removal-condition register.

---

## Known-open, so you do not rediscover them as surprises

- `segment_runs` reads a frame-counter wrap as a capture-run boundary. Measured
  effect: the mount probe used 264 of 456 frames on aug09/set-02 and still read a
  decisive fixed signature. Conservative, not corrupting — but it is wrong.
- The **per-set** compose still registers star-pair. Its own A/B measured only
  +0.019 roundness for +0.033 px FWHM, a wash. It is stated on the product
  (`REGMODEL=starpair`), not hidden. Decide it on its own evidence.
- A pilot build of `aug09/set-01` was running while `run_undistort_groups.sh` was
  edited. Bash reads scripts by byte offset. Its members may be unsolved and its
  tail is not trusted — **rebuild that set rather than reusing it**, and treat any
  member without a WCS as suspect.
- `ingest.json` for aug09 records `transfer-verified`, not source-verified: no
  source-side hashes exist for that night, so silent bit corruption was never
  checkable there.
- Filenames repeat after the counter wraps. The corpus is 6,938 frames into a
  10,000 cycle with zero collisions today. A frame's identity is
  (session, set, basename); the basename alone is not a key.

## Rules

- Official tools do every pixel operation and every measurement of the
  deliverable (`CLAUDE.md`, the bright line). Diagnostics are exempt — reading
  pixels to investigate is fine and always was.
- One knob per experiment, hypothesis first, and a killed hypothesis becomes a
  `docs/dead-ends.md` entry WITH its numbers.
- Report WIN or a clean NULL. Never "fixed" or "final" before it is measured, and
  never for anything aesthetic without the owner's eyes on the full-frame
  16-bit PNG.
- Do not delete raw frames. Do not `git push` without being asked.
- The data is a given: fixes live in the chain, never in a request for different
  acquisition.

## What to deliver

A cited `.md` at the repo root: what you rebuilt, what every acceptance
measurement read (with `n`), whether the fix held from raws, every audit finding
with its evidence, and what you changed. If the fix did NOT hold, that is the
most valuable result available — report it plainly with the numbers, and do not
soften it.
