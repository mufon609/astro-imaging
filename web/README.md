# web/ — the local front end (selection + framing, never judgment)

A **local-only** browser surface over the workspace (BACKLOG:`framing-radec`): browse
sessions and judge surfaces, and draw the product FRAMING rectangle whose
record the render chain consumes. No external service; the server binds
127.0.0.1 only.

## The contract (binding)

- **Everything served here is a SELECTION / NAVIGATION surface.** Aesthetic
  judgment happens ONLY on the full-frame lossless PNG16 files opened in the
  user's own viewers (README review contract). Previews are Siril-made
  downscales for *finding and framing*, never for judging — browsers render
  through 8-bit display paths.
- **The record is the product.** The crop UI captures a human decision into
  `datasets/<session>/framing_<product>.json` (both coordinate conventions +
  RA/Dec corners). It touches no pixels and decides nothing.
- **No render consumes an unverified framing.** `verify_framing.py` must
  stamp the record via Siril crop+stat first — the measured y-flip /
  zero-coverage guard (`docs/dead-ends.md`).
- **The mount declaration is the second sanctioned record write
  (user-ratified amendment).** `POST /api/mount` captures the human-declared
  `mount` ("fixed" | "tracked" — the one acquisition fact EXIF cannot record
  and no consumer may assume) into the set's `acquisition.json`, writing ONLY
  that field; `exif` stays tool-written by `acquisition.resolve()`, which
  preserves the declaration and fills the facts around it.
- **Execution from the site is gated per run (user-ratified amendment).**
  The site may EXECUTE a pipeline stage only from an explicit per-run user
  action — the operating loop's DECIDE step made clickable; never
  automatically, never on page load. An executed stage is one of a FIXED
  registry of the repo's pinned scripts (`serve.py` `/api/stages`), runs with
  the same records, gates and degrade-loudly behavior as a CLI run, shows its
  exact command with the run (validated and displayed as the job starts, with
  an on-demand preview that runs nothing — user-ratified one-click amendment),
  runs one at a time, and leaves its log under `sessions/.webjobs/`. The
  server stays 127.0.0.1-only.
- **One click may authorize one DECLARED multi-stage chain (user-ratified
  chain amendment).** The chain stages (`chain_set`, `chain_session` →
  `scripts/stack/run_set_chain.sh` / `run_session_chain.sh`) sequence the
  SAME pinned scripts through the durable core — preflight → frame QA →
  route-by-fingerprint stack → solve → SPCC → diagnostic judge surface —
  under full disclosure: every run prints its derived plan (route + reason,
  gates, the exact commands) before executing, and `plan=true` prints it
  running nothing. The chain STOPS wherever a decision is the user's —
  mount underivable (the instruments disagree or nothing measures; a
  decisive signature is adopted as mount_source=derived and announced,
  never stopped on) or CONTRADICT, an unroutable fingerprint, an unresolved
  flat. The measure phase ends at the READINESS REPORT — every ratified
  criterion GREEN/YELLOW/RED on ONE surface (readiness_report.py; the same
  evaluator behind /api/readiness and the set-page rail), RED exits 7 before
  anything builds — and the run click is that report's single approval (the
  stage passes --yes). The chain ENDS at the diagnostic judge surface:
  everything aesthetic
  beyond it (the render tier) stays per-rung and user-judged. QA defect
  flags do NOT stop it: the STANDING USER POLICY auto-culls flagged
  defect-side frames (they exclude like any obstruction), writes the
  recipe stack block with the flags as the why, and reports every cull
  decision inline and in the session end-summary; a hand-ratified stack
  block is never overwritten and always wins. Built products skip, so a
  re-click after resolving a gate resumes where it stopped.
- **The RENDER TIER is a per-run stage, deliberately not in the chain.** The
  chain still ends at the diagnostic judge surface; `render_tier` (phase
  `render`) is the aesthetic finish past it, reachable as its own gated click.
  It carries its own user gate, of exactly the kind this contract already
  requires: with no ratified `render` block for the name in the set's recipe it
  measures, writes `render_proposed`, prints it and STOPS (exit 7). Its KNOBS are
  not exposed as form fields — a browser checkbox is the wrong place to alter a
  look, and the recipe is where an accepted look is pinned. It refuses to
  overwrite an existing product without `overwrite`, so a ladder arm cannot
  destroy its own control.
- **A de-skied flat and the per-frame background step are one correction, and
  the form does not let them come apart** — but as of 2026-08-04 `sky_flat` is
  **NOT de-skied by default**, matching the chain. `--desky` was a 31x regression
  (12.4% vs 0.4% corner spread; `docs/dead-ends.md`) and is now opt-IN, for
  reproducing the defect only. The pairing logic is unchanged and still correct:
  the output NAME records the shape (`skyflat_<set>_desky.fit` when de-skied) and
  `stack_undistort` / `stack_undistort_groups` DERIVE `--desky` from the chosen
  flat's name rather than asking, so the two halves cannot come apart in either
  direction.

## Running it

```bash
python3 web/serve.py                 # http://127.0.0.1:8321/web/index.html
web/make_previews.sh <session>       # Siril-made thumbs + selection surfaces
                                     #   -> web/results/<session>/previews/
# draw the frame in the browser (crop.html), then verify the record:
python3 web/verify_framing.py <session> <product> \
    --map=<coverage_map.fit> --map-min=<members>   # coverage-map mode
#   or --min-floor=<ADU>                           # sibling-class sky floor
```

## Files

| file | role |
|---|---|
| `serve.py` | static server (repo root, read-only) + `GET /api/sessions` + `GET /api/session/<name>` (the joined read-only session model: per-set records normalized across the measured schema drift, surfaces with FITS-header frame counts confirmed against the recipes — metadata reads, never pixels — and approvals from git tags only) + `POST /api/framing` (writes the tracked record, `dry_run` supported; the only RECORD write) + the Tier-1 execution surface (`GET /api/stages`, `POST /api/run` — the gated per-click stage runner over the fixed script registry, `dry_run` returns the exact command — `GET/POST /api/jobs*` status, incremental logs, kill; job records persist as `sessions/.webjobs/<id>.json` and running jobs are re-adopted pid-checked after a server restart, so the one-at-a-time gate holds; `GET /api/version` reports the git rev + start time the running server was loaded on — the shell shows it, so a stale in-memory registry is visible) |
| `index.html` | the workspace shell: rail GROUPED work / results / evidence + hash-routed pages over `/api/session/<name>`. The Overview LEADS WITH THE NEXT ACTION — `/api/status/<session>` already returned per-stage `{state, why}` with specific evidence and the UI was showing only the state, on the Run page alone, discarding every why. Renders are their own page (`#renders`), not a section of Stacks. Chips carry hover help from a single `CHIP_HELP` map applied by a DOM pass, so a chip added later is covered. Exit codes read as plain language: a chain STOP (2/4/5/6), a product REGRESSION against the set's accepted baseline (8) and the render tier's proposal (7) are decisions, not crashes, and are styled as such — overview (router cards), per-set Frames tab (the cull DECISION with verbatim whys vs the post-stack CONFIRMATION against stack headers), culled rollup, surfaces (git-tag approvals; diagnostic-stretch caveat), sky objects, experiments ledgers, framing, read-only records viewer. Absent artifacts render as designed states naming their producer |
| `crop.html` | the item-12 framing UI: selection preview + existing crop-map reference boxes + drag/fine-tune a rectangle → POST the record |
| `make_previews.sh` | tool-driven preview generation (Siril load/autostretch/resample/savepng) + `previews/manifest.json` (native dims, exact scale, matched reference boxes) |
| `verify_framing.py` | the record verifier: Siril `crop`+`stat` against the coverage map (`Min >= members*1000`) or the product stack's sibling-class sky floor |
| `results/<session>/` | the durable output tree (gitignored data; see README "Data layout") |

**Renders are their own class, not stacks.** `render_<name>.fit` +
`judge/<name>_render.png`, modelled from the TRACKED record
(`qa_work/render_<name>.json`) rather than by parsing filenames — each record
names its own `linear_source`, so a render is attached to the stack it was
rendered FROM (longest-match, or a shorter product steals it). They are kept out
of the `stack_*` namespace deliberately: that namespace is modelled as integrated
stacks in the surfaces list, the solve/SPCC pickers and the frame-count
confirmation, none of which mean anything for a render.

**A record is not necessarily a JSON object.** `session_model` reads every
session-level `*.json`; a timeline record is legitimately an ARRAY
(`transparency_curve.json`). Calling `.get()` on one raised `AttributeError`
inside the model and **500'd the entire `/api/session/<name>` endpoint** — every
page for that session went dark on one record's shape, and stayed dark unnoticed
for a whole branch because nothing exercises the API. The reader now reports each
record's `shape` and `entries` instead of assuming. Worth a smoke test in CI: the
three staged sessions must return 200.

**Readiness is scoped to PROCESSABLE light sets, and says what it excluded.**
`stage_status` counted every set of kind `lights`, so july23's next action read
"frame_qa missing for: dew_chroma, set-00" — a records-only investigation directory with
no frame dir at all, and a 3-frame test burst. Neither can be processed by any stage, so
"next" pointed at work nobody could do. The scope is now the sets the SCRIPTS THEMSELVES
accept (`run_set_chain.sh`/`run_frame_qa.sh` refuse under 8 frames; `build_sky_flat.sh`
under 20), and the excluded sets are reported with their frame count and reason under the
next action — narrowed, never silent. The status payload carries this as `_scope`; keys
beginning with `_` are metadata, not stages, and both iterators skip them.

**Two things called "approved", named apart.** A *ratified look* is a set recipe's
`render` block naming a render, which is what makes the render tier execute instead of
stopping at its proposal — it makes the look reproducible. *git-approved* is a
`<session>-all<N>-<tag>-approved` tag: the record that you judged the product and
re-baselined it. A ratified look is NOT an approved render, and the UI now prints the
exact `git tag` command for any ratified-but-untagged render instead of stating "approval
only from the git tag" without the mechanism.

**Verdicts, not bare ratios.** `RENDER_RATIO_FLOOR_PCT` in `serve.py` owns this chain's
measured run-to-run floor (1.34% in the colour ratios, from two runs of ONE pinned
recipe — the neural stages are not bit-reproducible). A render's colour check returns
NULL at or below it — *unmeasurable here, explicitly not an improvement* — and
needs-eyes above. It never returns WIN: there is no control arm, only the render against
its own input layer.

**Judge surfaces that pair to nothing are reported, never renamed.** A name that misses
`<product>_<surface>` used to render as "no judge surface", which invites a needless
finish_render re-run. `unpaired_judge` lists them with the name that would pair. Nothing
is moved automatically: a judged artifact may be cited by a tracked record or doc.

Coordinate conventions, stated once and stored in every record: the browser
draws in **screen top-left origin**; Siril `crop`'s y-origin is the **bottom**
(`y_siril = H − y_screen − h`). The record carries both; verification uses the
Siril args. The UI's dashed reference boxes (e.g. the cov25 frame) are read
from `datasets/<session>/*/qa_work/*_map.json` records whose canvas matches
the product.
