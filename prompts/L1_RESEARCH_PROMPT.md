# Fresh-session brief — L1 research: settle the instrument and the doctrine BEFORE the rebuild

**SELF-RETIRING.** Delete this file in the commit that lands the result.

**You are NOT building arms in this session.** The L1 background-level experiment
is a full member rebuild — `--subsky-lights` fires per-frame on calibrated,
debayered lights *before* the geometric warp, so flipping it invalidates the
warp, registration, stack, compose, solve and SPCC. The owner has authorised that
rebuild and both arms, with time explicitly not a constraint. Your job is to make
sure it cannot be wasted.

**The measured reason this session exists.** The object-tilt session built a
complete instrument, ran it over 12 sets, and only then established that the
measurement was structurally impossible. Two blockers, either fatal, both
knowable in advance. That cost a session. L1's adoption gate has the same shape
of hole in it today, and this brief is scoped to find the holes while they are
still cheap.

## The blocking gap, verified live

**L1's adoption gate is "preservation of the frame-filling UNRESOLVED STARLIGHT"
and NOTHING IN THE TREE MEASURES IT.** Verified: `docs/dead-ends.md` cites
`qa_work/dust_identification.json` (july23, Gaia DR3 vs Siril, per-cell diffuse
floor tracking the unresolved-starlight prediction at R² 0.9631 over a 140-cell
external lattice) — that record went with the archived july23 session, and no
script under `scripts/` computes a per-cell diffuse floor or anything equivalent.

So the gate that decides whether L1 ships has no instrument. Settling that is
this session's first and largest job.

## What must be settled — three items, each currently a belief

### 1. The starlight-preservation instrument — build it, or document the gap

**Search the tools first and record what you searched.** "Every number came from
a tool" does not make an in-house analysis in-bounds, and a GUI-only name may
have a scriptable sibling — probe, never assume (`tilt`/`inspector` refuse,
`seqtilt` was the answer). Candidates worth probing, not an exhaustive list:
Siril's own statistics and photometry surface; `sep` (SExtractor's core, already
this repo's sole extractor, already in `~/.local/share/astrometry-venv`);
`source-extractor` 2.28.2 (installed, `BACKPHOTO_TYPE LOCAL`, `FLUX_APER`);
GraXpert; ASTAP. Gaia is available locally
(`~/.local/share/siril_catalogues/`) and astropy is installed.

If a tool does it, use the tool and stop. If none does, this is a **documented
gap** — say so explicitly, and then either build the gap-filler under the
ALLOWED rules (outside the deliverable pipeline, every pixel and every standard
measurement a tool's, only a derived result no tool provides, gates nothing,
carries a removal condition and its register row) or record that the gate is the
owner's eyes alone. **Both outcomes are acceptable; an unstated one is not**,
because the build session inherits whichever it is.

Note what the original instrument actually was, since it is the shape to match:
Gaia's own catalogue prediction against Siril's own per-cell measurement, over
an EXTERNAL lattice — external so the cells cannot move with the defect under
test (`docs/dead-ends.md` trap 3: a binning origin inferred from the detections
moves WITH the defect and flattens the profile as the defect worsens).

### 2. Degree 1 vs degree 2 — a belief that has been gating policy

`docs/dead-ends.md`, verbatim: *"the galactic-plane star field is frame-scale
curvature at wide focal, so `seqsubsky 2` is expected to absorb it and only a
first-degree plane or a full BGE to preserve it … **No controlled
degree-1-vs-degree-2 comparison on this data is on record** — no numbers, no
instrument, no n — yet this has been gating the background policy (and the
README class limit) as though it were a result."*

Settle its STATUS, at least. The registry names the test — one knob,
`seqsubsky 1` vs `2` on the same frames, judged on the instrument from item 1 —
and that test is cheap on a handful of frames, needing no rebuild. Run it if
item 1 yields an instrument. If it does not, say plainly that degree choice
rests on mechanism and vendor doctrine rather than this data, and record which.

**The build session needs this answer to size itself**: if degree 2 is a live
candidate it is a third arm, and that must be known before anything is built,
not after.

### 3. "Visible rings" — an unrecorded eye observation propping up the default

Same entry: stack-level-only BGE *"is reported to leave a structured residual
with visible rings and to eat the same frame-scale starlight, making per-frame
`subsky 1` the preferred step — 'visible rings' is an unrecorded eye observation
(no image, no metric, no n); treat the per-frame default as a reasonable prior,
not an established result."*

The owner has asked for BOTH arms — per-frame and on-stack — so this belief is
about to be tested properly whatever you find. What this session owes is its
status: is there a source for it (vendor docs, forum, our own history), or is it
folklore? Record the answer either way, because if the on-stack arm loses, the
record should say whether that was predicted or discovered.

## Standards-first — state the industry way, with its source

Every contract and design states the industry-standard way FIRST and deviates
only on a measured constraint, recorded. For this stage that means: what do
Siril's own docs say about per-frame versus on-stack background extraction and
about degree choice; what is PixInsight's DBE/ABE doctrine and where in the
sequence it sits; what the field's consensus order is (both vendors already put
background extraction BEFORE colour calibration — the repo records that). Cite
primary sources. Where our chain deviates, the deviation gets its reason.

## Refresh the pre-registration — it is stale

`datasets/aug06/experiments.jsonl`, `subsky_lights_restoration`, is written and
sound in shape: one knob, control named, hypothesis with what must SURVIVE,
instrument, surfaces. But its verdict reads **"OPEN — arm building"** and no arm
was ever built (verified: no `*subsky1*` product exists anywhere). It also
predates the from-raws corpus rebuild, so every path and every control it names
must be re-verified against what is on disk now.

Bring it current, and EXTEND it to the second arm the owner has asked for — the
on-stack background step — so the build session inherits one pre-registration
covering both arms with a falsifier for each. Do not water down what is already
there; the hypothesis's "what must SURVIVE" clause is the part that makes it a
real test.

## Fenced — do not re-derive or re-attempt

- **The flat-residual line is PAUSED by the owner** pending real flats. Do not
  touch it, and do not let a background question drift into a flat question.
- Raw-domain de-sky (`--desky` flat-side half): dead, 31× regression, and the
  two halves must never share a flag again.
- Degree ≥2 on UN-flat-fielded frames: dead on parity grounds. Item 2 above is
  about degree on CALIBRATED lights, which is a different question — do not
  conflate them, and do not cite the parity entry against it.
- A composite-level plane as the fix for the corner term: measured dead (a
  composite plane structurally cannot fit a corner-local term).
- GraXpert AI Division on a Milky-Way field; the self-referential flat class;
  additive matching for the corner term.
- **No acquisition answer.** The data is a given.

## Acceptance — executable, each with what you ran

1. The tool search is recorded — what you searched, what each returned, and the
   probe that proved it (a `help` listing is not evidence of headless support).
2. Item 1 lands as one of: a working instrument with a `--selftest` that
   falsifies its own mechanism in process (break it, watch it go RED, restore,
   watch it catch again), plus its removal-conditions row in the same commit; OR
   a documented gap with the gate restated as the owner's eyes.
3. Items 2 and 3 each land with an explicit STATUS — MEASURED (with numbers, n
   and instrument), MECHANISM, or DOCTRINE (with its source). No item may stay
   an unattributed belief.
4. The refreshed pre-registration covers BOTH arms, every path re-verified
   against disk, committed BEFORE the build session starts.
5. Five guards and every selftest PASS; `--plan` still walks a session clean.
6. `prompts/REPORT.md` updated; this file deleted in the same commit; the build
   brief's remaining unknowns listed explicitly so the next session knows what
   it is inheriting.

## Scope

**No arms, no rebuild, no member is touched.** If you find yourself starting a
build, stop — that is the next session, and it is authorised only once the gate
it will be judged by exists.

## Honest failure

If no tool measures starlight preservation and the gap-filler cannot be built
inside the ALLOWED rules, say so plainly — that is a finding, and it hands the
owner a real choice (their eyes as the sole gate, or a different acceptance
measure, which needs their ratification). **The NULL is the most valuable result
this program produces**, and it has banked several. Never
"fixed/final/matched/close".

Verify everything in this brief against the repo before relying on it.
