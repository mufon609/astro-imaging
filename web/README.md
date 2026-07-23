# web/ — the local front end (selection + framing, never judgment)

A **local-only** browser surface over the workspace (BACKLOG item 12): browse
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
  exact command before the run click, runs one at a time, and leaves its log
  under `sessions/.webjobs/`. The server stays 127.0.0.1-only.

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
| `index.html` | the workspace shell: rail menu + hash-routed pages over `/api/session/<name>` — overview (router cards), per-set Frames tab (the cull DECISION with verbatim whys vs the post-stack CONFIRMATION against stack headers), culled rollup, surfaces (git-tag approvals; diagnostic-stretch caveat), sky objects, experiments ledgers, framing, read-only records viewer. Absent artifacts render as designed states naming their producer |
| `crop.html` | the item-12 framing UI: selection preview + existing crop-map reference boxes + drag/fine-tune a rectangle → POST the record |
| `make_previews.sh` | tool-driven preview generation (Siril load/autostretch/resample/savepng) + `previews/manifest.json` (native dims, exact scale, matched reference boxes) |
| `verify_framing.py` | the record verifier: Siril `crop`+`stat` against the coverage map (`Min >= members*1000`) or the product stack's sibling-class sky floor |
| `results/<session>/` | the durable output tree (gitignored data; see README "Data layout") |

Coordinate conventions, stated once and stored in every record: the browser
draws in **screen top-left origin**; Siril `crop`'s y-origin is the **bottom**
(`y_siril = H − y_screen − h`). The record carries both; verification uses the
Siril args. The UI's dashed reference boxes (e.g. the cov25 frame) are read
from `datasets/<session>/*/qa_work/*_map.json` records whose canvas matches
the product.
