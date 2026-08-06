# Prompt for a fresh session — pipeline integrity. Companion to `AUDIT_FLAT_GRADIENT_PROMPT.md`

Two prompts came out of the july31 end-to-end run. The other one is about the
DATA — a 31% disagreement between the four sky flats, and whether it reaches the
deliverable. **This one is about the PIPELINE**: what it measured wrongly, what it
cannot measure yet, and one failure that was never diagnosed.

Read them in either order; they touch different files and can be worked
independently. If you only have appetite for one, **do the flat gradient first** —
it is the one that might be changing the pictures.

Paste everything below the line.

---

# STATE OF THE DATA — read this before planning anything

**Most derived data has been deleted. That is deliberate, and it is fine.** The
raws are all present, so anything removed is regenerable — but it costs a rebuild,
and several tasks below assume you will pay that rather than go looking.

**On disk:**

| | |
|---|---|
| `sessions/july31/{darks,set-01..04}/` | **2114 raw NEF** — the whole session, untouched |
| `sessions/july31/work/masters/` | master dark + the four per-set sky flats |
| `web/results/july31/stack_set-0{1..4}_full{,_spcc}.fit` | the four accepted per-set stacks |
| `web/results/july31/stack_all4_full{,_spcc}.fit` | the accepted 1760-frame combine |
| `web/results/july31/judge/*.png` | the five accepted judge surfaces |
| `web/results/july31/flat_gradient/` | the flat-ratio diagnostics |
| `datasets/july31/` | every tracked record, incl. `experiments.jsonl` |

**Gone, and NOT to be hunted for:**

- **All sub-stacks** (`work/groups_set-*`). The combine cannot be re-composed; it
  would need a full re-warp from raws.
- **Both single-pass control stacks** (`stack_set-01.fit`, `stack_set-02.fit`) and
  the **`--group=250` arm**. The route A/B and the dose-response cannot be re-read
  off disk — **their numbers survive only in `datasets/july31/experiments.jsonl`**,
  which is why that file is the authority for §1 and §3 below.
- **Every `_wcs.fit`.** No surviving stack carries WCS keywords. Re-inject with
  `scripts/calibrate/solve_field.py --inject=` if you need sky coordinates.
- **All work trees** (`work/undistort_*`, `work/flatbuild_*`, `work/render_*`).

**So: any comparison against a previous product means rebuilding that product from
raws.** A 500-frame set is ~90 minutes. This is expected and endorsed — "i don't
mind having to rerun any part of the process. slow and steady is the way to build
for this project." Do not design around avoiding a rebuild, and do not treat a
missing intermediate as a fault.

# What this is

july31 was run end to end from raw frames only — 1767 NEFs, four sets, no prior
artifact. The chain worked: four stacks, a 1760-frame combine, all five judge
surfaces accepted by the user. Along the way it produced a series of findings
about ITSELF, several of which turned out to be wrong, and the corrections are
more useful than the findings were.

Your job is the unfinished half. **Nothing here is a picture problem.** These are
measurement-integrity problems, and the first one gates the rest.

## 1. THE REBUILD-REPEAT FLOOR IS UNMEASURED — and it invalidates route claims

**Do this first. Every other route conclusion in the records is provisional until
it exists.**

The session compared two stacking routes (single-pass vs groups) and reported a
0.12–0.18 px improvement at one drift-axis station. It also compared two group
sizes and found a 0.05 px gap. **Neither number can be distinguished from
rebuild variance, because nobody has ever measured what a rebuild's variance is
on this chain.**

What IS measured, and does not cover it:

| floor | value | what it bounds |
|---|---|---|
| compose repeat | **0.00 px, bit-identical** (n=2, Siril `isub`) | re-composing UNCHANGED sub-stacks |
| darktable warp | **bit-identical** across a 3× load range (n=3) | the warp alone |
| stack-level (registry) | 2.06% star edge / 0.073% flat sky | separately REGISTERED stacks, a different chain |

None bounds a **full rebuild** through warp → register → per-group stack →
compose from the same frames. That is the missing number.

**The test**, already pre-registered in `datasets/july31/experiments.jsonl` under
`rebuild_repeat_floor_set01` with `verdict: null` — read that entry, it names the
decision rule so it cannot be fitted after the fact:

```
rebuild ONE set through the IDENTICAL route from the SAME frames, same masters,
same flat, same pinned lens model, to a distinct --out. Compare with:
  siril isub + stat            whole-frame flux
  regional_stat 400/200        is the difference structured?
  star_shape (seqtilt)         truncated-mean FWHM, off-axis, sensor tilt
  star_stations along+1300     THE measure the route claim rests on
```

Pre-committed decision rule: repeat spread ≪ 0.12 px → the route effect survives
as measurable. Repeat spread ≈ 0.12 px → **every route claim from that session is
withdrawn**, including the one written up as a "narrow replicated win". Bit-
identical → the whole chain is deterministic and README's per-frame-sweep
exemption is wrong too.

**This starts from raws** — see STATE OF THE DATA above; no sub-stack or control
survives. ~90 minutes for a 500-frame set, and still the cheapest thing here,
because it decides whether three other results mean anything. Note you are
building BOTH arms fresh: the original is gone too, so this is a clean same-arm
repeat rather than a comparison against an aging product.

## 2. A BUILD FAILED AND WAS NEVER DIAGNOSED

A rebuild died at `WARP FAILED pp_c_00012` with its entire work tree missing. The
cause is **unrecoverable** — the builder redirected darktable-cli to `/dev/null`,
so the only surviving evidence was a frame name.

Two candidate mechanisms, neither established, and **do not pick one without
evidence**:

- **Concurrent builders.** `run_undistort_pipeline.sh` derives its work dir from
  SESSION and SET alone and opens by `rm -rf`-ing it. A second invocation for the
  same set destroys the first's tree mid-flight; the first then fails somewhere
  arbitrary with its inputs gone, which reads as a tool failure.
- **`BACKLOG:flatpak-race`.** Measured: two rapid-fire `siril-cli` loops running
  concurrently die after ~10 min, one occurrence in ~150 paired invocations, and
  the failing script prints nothing.

Both are now either prevented or diagnosable (commit `63108c7`: darktable's
stderr is kept in `$P/dt_last.log` and printed on failure; a pid lock refuses a
second builder). **If it recurs, you will have the error message the last
occurrence threw away.** Do not assume it is fixed — nothing was diagnosed, only
instrumented.

## 3. WHAT THE ROUTE EXPERIMENTS ACTUALLY ESTABLISHED

Read `datasets/july31/experiments.jsonl` end to end before touching this. The
short version, because the headline changed three times:

- **seqtilt off-axis 0.42 → 0.18 on set-01 did NOT replicate** (set-02: 0.44 →
  0.45). Worse, `seqtilt` is documented in the registry as *blind to a
  drift-aligned band*, which is the exact defect class under test —
  `star_stations.py` exists because of that blindness. The instrument was chosen
  after seeing which number was bigger.
- **`along+1300` was selected post-hoc from nine stations.** Under a null where
  stations move independently, P(≥1 of 9 agreeing in direction across two sets)
  ≈ 0.92. One-in-nine replicating is what noise looks like.
- **The `group=250` dose-response FALSIFIED the mechanism.** Prediction was that
  250 lands between single-pass and 100, monotonically. It landed outside both
  intervals (FWHM 2.900 vs [2.950, 3.070]; roundness 0.8710 vs [0.8300, 0.8640]).
- **What survives:** every groups arm beat single-pass at that station on two
  sets. *Direction* replicates. Magnitude is unestablished and gated on item 1.
- **The route decision does not rest on any of this.** It rests on
  **composability** — the groups route leaves sub-stacks a cross-set combine can
  reuse. That is why the 1760-frame combine exists without re-warping.

## 4. THE COMPOSABILITY DECISION WAS REVERSED BY A CLEANUP

The session rebuilt all four sets on the groups route specifically so the
sub-stacks would survive and a deep combine would never need a re-warp. A later
cleanup **deleted the sub-stacks**. The reasoning given — they were built on
flats now under investigation, so they would be rebuilt anyway — is defensible.

**Flag it to the user before assuming either way.** The combine on disk
(`stack_all4_full.fit`, 1760 frames) can no longer be reproduced without
re-warping 1767 frames, which is the exact cost the route change was made to
avoid. If the flat investigation changes the flats, that is moot. If it does not,
the sub-stacks should come back.

## 5. THE DWELL FLOOR IS LIVE BUT UNVERIFIED ON EVERY SET

`run_undistort_groups.sh` now derives its group size to keep every transient
below GESD's outlier-fraction cap: `GROUP ≥ ceil(max_dwell / 0.30)`, because
`rej g 0.3 0.05`'s first parameter is the maximum fraction GESD will even
consider rejecting. A transient dwelling past that is not rejected at all.

It reads `max_dwell` from the set's `anomaly_audit.json`. **The chain never runs
`anomaly_audit.py`**, so every july31 set reports:

```
dwell floor: NOT CHECKED — no anomaly_audit.json for this set, so the
'transient is a clear minority' half of the group-size rationale is UNVERIFIED.
```

All transient data in the records is **recovered from a pre-reset audit** at
`01dd19c^`, taken against a different cull. It has been consistent every time it
was checked, which is exactly the condition under which people stop re-checking.
set-03 carries ten transients with a dwell spectrum [1,1,3,4,8,9,11,17,20,27]; the
27-frame satellite sits at **90% of the cap** at group=100.

`README.md:576` documents the audit as part of the per-set prep. The chain omits
it. That is now a *functional* coupling, not a documentation gap.

## 6. THE PATTERN THAT PRODUCED MOST OF THE ERRORS

Six checks-that-cannot-fail surfaced in one session, and **four wrong conclusions
came from truncated shell commands** — `tail -1` on a file holding six matching
lines, `ls | head -5` on a directory whose fifth entry was the file in question,
a grep that matched nothing while the next line asserted the conclusion anyway.

The registry now carries the rule (*break the mechanism, watch the assertion go
red, restore*) and `lens_preflight.py --selftest` implements it — it neutralises
its own masking in-process, asserts the incident reproduces, restores, asserts it
is caught again.

**The actionable form is not another registry entry.** Every one of these came
from hand-rolling a check because invoking the tool was more effort. What works
is making the correct check cheaper: `--plan` exercising the guards that can
refuse a run, `--json` recording what was actually applied, `--selftest` in the
sweep. Prefer that shape over discipline.

**`BACKLOG:guards-and-ci` is the standing gap** — `check_bitdepth.sh`,
`check_calibrate.sh`, `check_stack_rejection.sh` and two `--selftest`s all fail
loudly and **nothing runs them automatically**. They were run by hand after every
change in that session. A runner replaces the discipline.

## 7. SMALLER, VERIFIED, UNFIXED

Each confirmed against the code, none of them urgent:

- **`fov >= 10`** — the route key, written at four sites, single-sourced nowhere.
  A fixed tripod at 200 mm (≈6° field) exits 5, unroutable, despite being the
  same class with *more* pixel drift. Route on measured `drift_px` instead; the
  fingerprint already computes it.
- **`mount` is derived and then ignored.** `fingerprint.mount_check` returned
  `measured: fixed` at 15.0493 deg/hr against a sidereal 15.041, confirmed on all
  four sets within 0.6% — before any human spoke. `run_set_chain.sh` computes
  `MOUNT_EFF=${MEASURED:-$MOUNT}`, routes the *plan* on it, then refuses to act
  because the declaration string is absent. The policy belongs in
  `acquisition.resolve()` (the gate every consumer routes through), accepting a
  drift-solve verdict, keeping the declaration as an override that still raises
  CONTRADICT, and still stopping on INDETERMINATE. Also: `mount` is modelled
  per-set, so one tripod on one night pays for four probes.
- **The master dark's rejection is hardcoded** `rej 3 3` in
  `siril/master_dark.ssf:14` — 347 darks get winsorized where the repo's own
  doctrine (`stack_rejection.sh`) says GESD above 50. Lights route through the
  shared helper; masters do not.
- **Registration transform and interpolation are not pinned.** No `-transf=` or
  `-interp=` in the generated `.ssf`, so both come from Siril's defaults. TOOLS.md
  names homography + lanczos4-with-clamp as doctrine. A Siril update changes
  stacks silently.
- **`frame_metrics.json` is execution-order dependent** — it prefers the solved
  plate scale only if the fingerprint already carries one. Run QA before the mount
  probe and every `fwhm_arcsec` inherits a 2.8% error (17.5031 nominal vs 18.003
  solved). Self-documented via `pixel_scale_source`, never re-derived.
- **A cross-set product has no home.** `finish_render.sh` requires `--set`, so the
  1760-frame combine's SPCC record landed under set-03. `datasets/README` reserves
  session-level records for exactly this and the finish stage cannot write one.
- **`check_stack_rejection.sh` is mode 100644** — `./scripts/…` is
  permission-denied; only `bash …` works.

## 8. WHAT IS NOT BROKEN — do not spend time here

Verified this session, with numbers:

- **The mount is measured, not assumed.** Four two-window drift solves, worst
  deviation 0.6% from sidereal. `fixed` confirmed on every set.
- **The optics are correct and now recorded.** The installed model is the pinned
  incumbent; `lens_preflight --json` writes per-set provenance. Every july31
  product was built after the model was restored — verified by timestamp against
  the build times.
- **The auto-cull was right for a reason it never checked.** set-01's seven
  flagged frames are exactly the block containing the only three capture gaps in
  the set (83 s / 119 s / 127 s) — the rig being set up. Quality flags and cadence
  agree. `acquisition.timeline()` already computes the latter and the cull does
  not consult it; that is corroboration worth wiring, not a defect.
- **All four sets take the identical route with identical parameters.** Verified
  by comparing the generated commands character-for-character. Only the cull (data)
  and the per-set flat (required) differ.

## Rules

The binding rules in `AUDIT_FLAT_GRADIENT_PROMPT.md` apply here unchanged: one
variable per run, no pipeline or doc changes ahead of a controlled test, official
tools do the pixel work, and a clean NULL is a real result. Two additions specific
to this prompt:

1. **Read `datasets/july31/experiments.jsonl` before forming any view on the route
   work.** Three verdicts on the same experiment are in there, superseding each
   other, with the errors stated. The last one is the one that stands.
2. **Do not quote a number from a command whose output you truncated.** It is the
   single most common error in the session that produced this prompt, and it
   produced four wrong conclusions in a row — including one that briefly looked
   like the shipped optics were wrong.
