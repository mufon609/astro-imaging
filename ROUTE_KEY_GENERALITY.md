# The route key — from one rig's field width to a measured excursion

The router decided a set's chain with `fov >= 10`, written at six sites and
single-sourced nowhere. That key was **multiplied** and it was **physically
inverted**. It is now one derivation, `scripts/lib/route.py`, on the quantity
the mechanism is actually about: the **sky excursion over the set's span as a
fraction of the field**. Every one of the 12 real sets routes exactly as before.

---

## 1. What was wrong, verified before anything was touched

Six live copies, confirmed by the registered grep:

    scripts/lib/fingerprint.py:245        (_label width band)
    scripts/lib/fingerprint.py:291        (the route branch)
    scripts/stack/run_set_chain.sh:165    (initial route decision)
    scripts/stack/run_set_chain.sh:504    (post-preflight re-derivation)
    scripts/qa/readiness_report.py:183    (readiness evaluator)
    web/serve.py:1712                     (the web rail's set position)

**The physics.** The undistort route exists because the true frame-to-frame map
of a drifting field is `distort ∘ H ∘ distort⁻¹` (Kukelova et al., CVPR 2015,
"Radial Distortion Homography"). For an *ideal* rectilinear lens a pure camera
rotation is EXACTLY an 8-DOF homography (Szeliski, *Image Alignment and
Stitching* §2.3 — stars at infinity, sky rotation SO(3)), so the only residual an
optimal global fit leaves is unmodelled radial distortion: a star displaced ∝
radius samples a *different* local distortion as it drifts, and no global fit
absorbs the difference. `docs/wide-field-untracked-registration.md` states the
consequence directly — **"the residual scales with TIME SPAN, not frame count"**.

Field width does not appear in that mechanism, and keying on it inverts it. A
fixed mount sweeps `0.2507 × cos(dec)` °/min *whatever the focal length*, so the
fraction of its own field a set crosses per minute is `0.2507 × cos(dec) / fov`
— **larger for a narrow field**. The 10° floor excluded precisely the sets with
the most drift.

| fov | sky crossed per minute, as a fraction of the field (dec 0) | 30-minute set |
|---|---|---|
| 28.6° (this corpus) | 0.0088 | 0.26 |
| 10° (the old floor) | 0.025 | 0.75 |
| 2° (the refused case) | 0.125 | 3.8 |

## 2. The key

    drift_frac = (sky_sep_deg / probe_span_min) × set_span_min / fov_deg

| term | instrument |
|---|---|
| `sky_sep_deg` | haversine of two astrometry.net solves — `scripts/qa/mount_probe.sh` → `fingerprint.inter_frame_drift.sky_sep_arcsec` |
| `probe_span_min` | the two solved frames' capture epochs (EXIF / `DATE-OBS`) |
| `set_span_min` | the set's own capture span — `acquisition.exif.time_span_s` |
| `fov_deg` | plate scale × frame width — `scripts/lib/acquisition.py` |

Every term is a tool's measurement; `route.py` only divides them. The *rate*
comes from the probe window and is extrapolated to the **set's** span, because
the registration unit is the set, not whichever window the probe happened to fit
inside the longest continuous run.

### Why an angle and not `drift_px` — the finding that shaped the key

The prompt proposed keying on the recorded `drift_px`. **That number is not a
sensor-pixel count.** Camera raws are solved on Siril's extracted GREEN plane —
half the full-res grid — so the probe's own scale reads **35.28–36.28 arcsec/px
against the sensor's 16.979**, a factor **2.078–2.137** across this corpus. It is
documented in the probe's own record (`mount_probe.json` `domain_note`: *"px
figures are green-px at the solve's own scale"*).

So the same physical excursion reads **half as many "px"** on an OSC raw as on a
mono FITS frame solved at native scale. A px threshold would mean two different
physical things on two rigs — the exact rig-specific defect this work exists to
kill, wearing a new costume. An angle over an angle is free of the pixel grid,
of binning, and of the debayer path. `route.py --selftest` asserts the property:

    [PASS] drift_frac is identical on the green-plane and native grids
           — 0.2011 both; drift_px would read 575.3 vs 1220.2

## 3. The threshold — `drift_frac >= 0.05`, and what kind of number it is

**It is a floor of EVIDENCE, not a quality knee.** No knee has ever been
measured in this repo, and the residual is monotonic in drift. Inventing one by
extrapolating from a single measured point would be swapping one magic constant
for another — and it would have moved two corpus sets' routes on the strength of
an unmeasured extrapolation. 0.05 is the **smallest excursion at which this repo
has measured the term present**:

- the class was established at **drift_frac 0.247** (43 min, ~1500 px at
  18.02″/px across a 30.35° field): Siril `seqtilt` off-axis aberration
  **0.57 → 0.31 px** with the fitted lens model at 54 frames, **0.25 px** at 168;
- the shortest arm measured on the mechanism is the **9-min / ~310 px window =
  drift_frac 0.051**, whole-frame majFWHM **3.87 px** against the full span's
  **4.74 px** — better, and still the same mechanism. Below 0.051 the repo has no
  measurement, so the router claims none.

*(The short-window arm's per-radius numbers are deliberately not quoted: they
came from the retired in-house radial metric, `docs/dead-ends.md` trap 3.)*

**The key under-counts, in two directions — which is why the floor sits at the
bottom of the measured range rather than inside it:**

1. the total `-framing=min` trim runs **1.16–1.29× the pure translation** in
   every measured set (field rotation + warp border), so a set reading 0.05
   really sweeps 0.058–0.065 of its field;
2. a set whose probe windowed inside its longest continuous run has its re-aim
   excursion excluded from the rate.

**Below the floor a fixed mount routes `standard`, not to a stop.** `standard` is
*defined* by "no inter-frame drift to fight", and an excursion smaller than the
smallest one the term has ever been measured at is that condition. Undistorting
there is not free: it is a second interpolation pass, and with an *unfitted*
(community) lens model it MEASURED an introduced centre band — **5.30 px**
majFWHM at the frame centre against the uncorrected control's **4.03 px**
(`star_stations`, `docs/wide-field-untracked-registration.md`). This *shrinks*
the unroutable class rather than growing it; exit 5 survives exactly where
CLAUDE.md's evidence gate puts it — the mount signature is neither fixed nor
tracked, or the key's own inputs were never measured.

**Removal condition** (registered in `BACKLOG.md` in the same commit): the floor
retires the day a measured knee exists — an undistort-vs-homography A/B at two
drift fractions below 0.25, closing where the removable term drops under the
route's own irreducible residual (0.25 px off-axis aberration at full depth). The
*key* is mechanism-derived and does not retire with the floor.

## 4. The single-source design

`scripts/lib/route.py` — one definition, `DRIFT_FRAC_MIN = 0.05`, with the
derivation, the numbers and the removal condition in its own docstring.

| consumer | how it gets the key |
|---|---|
| `fingerprint.py` `_label` + route branch | `import route` → `route.derive()` |
| `run_set_chain.sh` initial decision | the facts block `import route` → `route.from_records()` |
| `run_set_chain.sh` post-preflight re-derivation | shells out to `python3 scripts/lib/route.py <session> <set>` |
| `readiness_report.py` `evaluate()` | `import route as _route` → `from_records()` |
| `web/serve.py` `_set_position()` | `_route_block()` → `route.from_records()` |

`disk_budget.sh` is the precedent and it settles a design question the prompt
left open. It asks for the fingerprint record to carry the route so consumers
can **read** the decision rather than re-derive it. The record now does carry it
— `fingerprint.json` gained a `route` block with the route, the key's value, the
threshold, the terms and the provenance, so every routing decision is auditable
from the tracked record:

```json
"route": {
 "route": "undistort-groups", "key": "drift_frac",
 "value": 0.0829, "threshold": 0.05,
 "terms": {"sky_sep_deg": 2.3717, "drift_deg_per_min": 0.1831,
           "probe_span_s": 777.0, "set_span_s": 777.0,
           "fov_deg": 28.6, "span_extrapolated": false},
 "provenance": "drift_frac = sky excursion / field width, from astrometry.net
   two-window solves (scripts/qa/mount_probe.sh) + header facts
   (scripts/lib/acquisition.py); threshold and derivation in scripts/lib/route.py"
}
```

**Consumers still call the function rather than trusting that block** — a
recorded, reasoned deviation from the prompt's suggestion. `disk_budget.sh`'s
precedent is a shared *derivation* (`undistort_frame_mib` is called, never
cached), and the failure modes differ: a shared derivation cannot go stale, a
cached decision can. Reading a record written under an older threshold is a new
way for the same defect to come back. The block is a **record**, not an oracle.

## 5. The 12-set before/after route table

`run_session_chain.sh <session> --plan` per session, routes diffed. `‡` = the
probe windowed inside the longest continuous run, so the rate is extrapolated to
the set's own span.

| set | frames | span s | sky swept ° | °/min | **drift_frac** | × floor | route before | route after |
|---|---|---|---|---|---|---|---|---|
| `july31/set-01` | 507 | 1838 | 5.75 | 0.188 | **0.2012** | 4.02× | `undistort-groups` | `undistort-groups` |
| `july31/set-02` | 500 | 1497 | 4.57 | 0.183 | **0.1599** | 3.20× | `undistort-groups` | `undistort-groups` |
| `july31/set-03` | 500 | 1497 | 4.55 | 0.182 | **0.1591** | 3.18× | `undistort-groups` | `undistort-groups` |
| `july31/set-04` | 260 | 777 | 2.37 | 0.183 | **0.0829** | 1.66× | `undistort-groups` | `undistort-groups` |
| `aug06/set-01` | 500 | 1497 | 4.58 | 0.184 | **0.1602** | 3.20× | `undistort-groups` | `undistort-groups` |
| `aug06/set-02` | 500 | 1497 | 4.60 | 0.184 | **0.1607** | 3.21× | `undistort-groups` | `undistort-groups` |
| `aug06/set-03` | 500 | 1497 | 4.60 | 0.184 | **0.1609** | 3.22× | `undistort-groups` | `undistort-groups` |
| `aug09/set-01` | 500 | 1497 | 4.60 | 0.184 | **0.1610** | 3.22× | `undistort-groups` | `undistort-groups` |
| `aug09/set-02` | 456 | 1365 | 2.44 ‡ | 0.186 | **0.1476** | 2.95× | `undistort-groups` | `undistort-groups` |
| `aug09/set-03` | 500 | 1497 | 4.74 | 0.190 | **0.1659** | 3.32× | `undistort-groups` | `undistort-groups` |
| `aug09/set-04` | 500 | 1497 | 4.63 | 0.186 | **0.1619** | 3.24× | `undistort-groups` | `undistort-groups` |
| `aug09/set-05` | 500 | 1497 | 4.69 | 0.188 | **0.1641** | 3.28× | `undistort-groups` | `undistort-groups` |

    diff <before> <after> → no output
    PASS: 12/12 identical

Range **0.083–0.201**, nearest the floor **1.66×**. No set sits near the
boundary. `aug06/set-00` (the spare-frames bucket, `drift_frac` 0.114) is never
enumerated as a light set, before or after — verified, 0 mentions in the aug06
plan.

## 6. Fixtures — the classes the old key got wrong

`scripts/lib/route.py --selftest` is the durable form (tracked, re-runnable, and
its corpus row reads the *tracked records*, not restated numbers). Each fixture
is stated in the **record's own shape** and goes through the same `derive()` the
chain calls.

```
  [PASS] corpus: 12 real sets all derive undistort-groups — nearest the floor: july31/set-04 at 0.0829 = 1.66x
  [PASS] 200 mm / APS-C fixed (fov 6.74 deg) routes to the undistort class — drift_frac 0.1748
  [PASS] fixed, fov 2.0 deg routes to the undistort class — drift_frac 0.376
  [PASS] mono/tracked (fov 0.88 deg, no drift record) routes standard — tracked mount: no inter-frame drift to fight
  [PASS] fixed but below the floor routes standard, not to a stop — drift_frac 0.0263
  [PASS] unclassified mount signature -> no route (the caller stops)
  [PASS] fixed but drift never measured -> no route, naming the probe
  [PASS] drift_frac is identical on the green-plane and native grids — 0.2011 both; drift_px would read 575.3 vs 1220.2
  SELFTEST PASS
```

### The 200 mm case, through the LIVE chain

Fixture discipline per `docs/dead-ends.md` ("a fixture's decoy must match the
scanner's own pattern"): the fixture supplies **only instrument output** — an
`acquisition.json` and a `mount_probe.json` in `mount_probe.sh`'s own schema, two
solves 300 s apart at dec +20. Everything else is derived by the live code, and
the run is `run_set_chain.sh --plan`, not a call into the function.

The live fingerprint CONFIRMed the mount off the fixture's solves (RA rate
**15.0408** deg/hr vs sidereal 15.041), then:

```
[chain set-01] PLAN — route: undistort-groups — fixed mount: the sky sweeps 0.175
  of the field over the set (1.18 deg at 0.236 deg/min across a 6.74 deg field),
  at or above the 0.05 floor the distortion term is measured at …
```

The retired key, run on the identical fixture inputs from `git show HEAD`:

```
OLD key on the same fixture:
  label     : untracked, normal, drifting 210 px/min
  route_hint: unclassified — measure before routing
  chain test: fov 6.74 >= 10 -> False -> stop-unroutable (exit 5)
```

### The mono/tracked class, through the LIVE chain

`datasets/colonnello-m20/lights_Red`'s own records (ASI mono, 1150 mm, 0.88°
field, tracked CONFIRMed by the trail-vs-roundness instrument at 538× margin,
`inter_frame_drift: null`):

```
[chain set-01] PLAN — 15 frames | mount 'tracked' | fingerprint: tracked, 0.88 deg field (CONFIRM)
[chain set-01] PLAN — route: standard — tracked mount: no inter-frame drift to fight -> calibrate / register / stack
```

## 7. Fire test — every consumer moves together

Flip `DRIFT_FRAC_MIN` to 0.25 (above the whole corpus), probe all five
consumers, restore.

| | floor 0.05 | floor 0.25 | restored 0.05 |
|---|---|---|---|
| `route.py` CLI *(chain: post-preflight re-derivation)* | `undistort-groups` | `standard` | `undistort-groups` |
| `run_set_chain.sh --plan` *(chain: initial decision)* | `undistort-groups` | `standard` | `undistort-groups` |
| `readiness_report.py` | `GREEN undistort-groups — drift_frac 0.2012 vs floor 0.05` | `GREEN standard — … vs floor 0.25` | `GREEN undistort-groups — … vs floor 0.05` |
| `serve.py` `_route_block` | `undistort-groups \| 0.2012 vs floor 0.05` | `standard \| … vs floor 0.25` | `undistort-groups \| … vs floor 0.05` |
| `fingerprint.py` record | `undistort-groups` | `standard` | `undistort-groups` |

No copy stayed behind, in either direction.

**A test artifact worth recording, because it made the first run lie.** `0.05` →
`0.25` is a **same-length** edit, so the source file's size does not change; if
the rewrite lands in the same second as the previous one, CPython's `.pyc`
validation (mtime + size) passes and every *importing* consumer reads **stale
bytecode**. The first fire test therefore showed four consumers "not moving back"
— indistinguishable from the defect under test. Only the `route.py` CLI moved,
because a script run as `__main__` is never served from `__pycache__`. Confirmed
directly:

    source: DRIFT_FRAC_MIN = 0.05
    route.py size=17142 mtime=1786539998
    route.cpython-313.pyc size=18766 mtime=1786539998
    module import reads: 0.25          <- stale
    after clearing pycache:  0.05

A fire test on a same-length constant must clear `__pycache__` between flips.

## 8. The two refusals

Both **name their class**; neither was handled, and the reason is scope — the
prompt's own rule is *"ROUTING ONLY — no builder behavior changes"*, and both
fixes are builder/chain-wiring work. Both are registered in
`BACKLOG.md:route-recommendation` with what closes them.

### 8.1 Real flats on the undistort route

A structural finding: **the chain's exit 6 is unreachable on the one-click
path.** `readiness_report.py` carries the same criterion and goes RED first
(exit 7) — so the wording had to be fixed in *both* places, and the readiness row
is the surface the user actually meets. What it now says:

```
RED  masters   real flats staged (flats) and the route is undistort-groups
     [session staging] Not a data defect — the opposite. The chain's undistort
     dispatch carries one flat source, the per-set SKY flat (a median of the
     set's own lights), and will not silently prefer it over flats that were
     shot. The BUILDER has no gap: it takes any master via --flat=. Resolve by
     building the master flat from the staged dir (Siril: convert -> calibrate
     with the matched dark-flat/bias -> stack rej 3 3 -norm=mul), then run
     scripts/stack/run_undistort_groups.sh --dark= --flat=<that master>
     directly; the chain prints the exact two commands at its own exit 6.
     Closing it for good is chain wiring, not a builder change —
     BACKLOG:route-recommendation
```

The chain's own exit 6 (defence in depth, and where the literal commands are)
prints the resolved paths and exits 6. Demonstrated on a fixture with real
`july31` raws (11 frames spanning the full 1820 s window, `drift_frac` 0.1992)
plus a staged `flats/` dir.

*Deliberately NOT done:* silently substituting the sky flat when real flats
exist. That would discard the frames that were shot to avoid the sky flat's own
open defect (the object carrying the sky's spatial profile, measured 3.11% at
241σ).

### 8.2 FITS lights on the undistort route

The old failure was `run_undistort_pipeline.sh` exiting with `no raw frames under
<dir>` — true, and pointing at a staging mistake that did not happen. The stop is
now taken in the chain **before a master is spent**, exit 9:

```
[chain set-01] STOP: this set's lights are FITS (10 frames), and the derived route is 'undistort-groups'
[chain set-01]   The frames and the route are BOTH right — the gap is between them: the
[chain set-01]   undistort builders (run_undistort_groups.sh / run_undistort_pipeline.sh)
[chain set-01]   glob camera raws only, because the route's first stage is darktable's
[chain set-01]   lens correction and darktable reads raws, not FITS. Nothing is staged wrong.
[chain set-01]   Next step, either:
[chain set-01]     1. run the standard route on this set — scripts/stack/run_pipeline.sh …
[chain set-01]        (registration without the undistort stage; the drift-distortion term
[chain set-01]        stays in, which is what the route existed to remove), or
[chain set-01]     2. leave it until the undistort route accepts FITS lights — that is a
[chain set-01]        BUILDER change (a FITS path around the darktable stage), not a routing
[chain set-01]        one, and it is the open capability, not a defect in this set.
>>> chain exit code: 9
```

Both builders were given the same diagnosis for a direct invocation, and
`run_undistort_groups.sh` gained a frame-count guard it did not have — a FITS set
previously fell through to `cullspec`'s *"cull resolution failed or left no
frames"*, a third wrong diagnosis.

The fixture is real FITS with real headers (10 frames, 600×400, 200 mm @
3.921 µm → 4.044 ″/px, `DATE-OBS` spread over 60 s) so the **live** acquisition
derivation reads them — a hand-written `exif` block is (correctly) overwritten by
the preflight, which the first attempt proved. Note it is a **0.67° field**: the
old key refused it outright as unroutable, so this refusal is only reachable
*because* the new key routes it.

## 9. Declared consequences beyond the 12 sets

- **`july26/set-01`** (262 s span, 28.6° field) will route `standard` once
  probed, where the old key sent it to undistort: 4.4 minutes of a fixed mount
  sweeps ~3.8% of that field, below the floor. Its frames are off-rig, so this is
  a prediction of the key, not a measured route change.
- **`july26/set-01`, `july26/set-02`** had no `fingerprint.json` at all; the
  refresh created them. They record `route: null` with the reason naming the
  drift probe — honest, where the old key would have routed them with no drift
  measurement at all.
- **A human-declared fixed set with no probe** used to route on `fov` alone.
  It now needs the key's instrument — so the chain **runs the two-window drift
  probe in the measure phase** rather than stopping (a measurable excursion is
  not a question for a human; CLAUDE.md's evidence gate). The 12 corpus sets
  already carry the probe record, so nothing re-runs.
- **`fingerprint.json` schema:** `route_hint` (prose, consumed by nobody) is
  replaced by the structured `route` block. Every record refreshed; the label
  now reads `untracked, 28.6 deg field, sky sweeps 0.201 of it` — the old
  `drifting 19 px/min` was green-plane px/min, the same rig-dependent number the
  key was moved off.

## 10. Files changed

| file | change |
|---|---|
| `scripts/lib/route.py` | **new** — the single source: key, threshold, derivation, provenance, removal condition, `--selftest` |
| `scripts/lib/fingerprint.py` | imports `route`; `_label` keyed on the excursion; route branch → `route.derive()`; `route_hint` → the `route` block |
| `scripts/stack/run_set_chain.sh` | both route sites read the single source; runs the drift probe when the key is unmeasured; exit 5/6 reworded; exit 9 added; real-flat and FITS refusals named |
| `scripts/stack/run_undistort_groups.sh` | frame-count guard + accurate FITS diagnosis |
| `scripts/stack/run_undistort_pipeline.sh` | accurate FITS diagnosis |
| `scripts/qa/readiness_report.py` | imports `route`; route row states the key's value vs floor; the real-flats RED row names its class and the resolving step |
| `web/serve.py` | `_route_block()` imports the single source; position + unroutable evidence from it |
| `datasets/*/*/fingerprint.json` | refreshed onto the `route` block (12 corpus + 3 mono/tracked + 2 july27 + 2 new july26) |
| `datasets/README.md` | `route_hint` → the `route` block, with why consumers still call the function |
| `docs/pipeline-wide-field-untracked.md` | §3 route key, §1 flat stop, §10 exit table (exit 9) |
| `BACKLOG.md` | `routing-generality` removed; `route-recommendation` carries the two named refusals; the floor's removal condition registered |
| `prompts/ROUTING_GENERALITY_PROMPT.md` | retired (`git rm`) |

## 11. Acceptance

| # | check | result |
|---|---|---|
| 1 | `grep -rniE "fov[^0-9]*>= *10" scripts/ web/` | **PASS** — no match; the key is drift-based with no fov clause left |
| 2 | 12 real sets route identically | **PASS** — diff empty, 12/12 |
| 3 | the 200 mm case routes | **PASS** — `undistort-groups` via the live chain; the old key gave exit 5 on identical inputs |
| 4 | mono/tracked still routes standard | **PASS** — `standard` via the live chain on `colonnello-m20`'s records |
| 5 | fire test on the single source | **PASS** — all 5 consumers move together and back (`__pycache__` caveat recorded) |
| 6 | both refusals demonstrated | **PASS** — exit 7/6 (real flats) and exit 9 (FITS), each naming its class and next step |
| 7 | `set-00` never enumerated | **PASS** — 0 mentions in the aug06 plan |
