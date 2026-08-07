# Fresh-session prompt — the docs/ deep-dives cleanup pass

Read `CLAUDE.md` first — it is the briefing and the read order. Then read
`docs/README.md` (the deep-dive rules: findings GRADUATE into operating docs;
docs/ must not drift from them) and this file fully before touching anything.

## The job

Execute the docs/ deep-dives cleanup — the third pass of the repo-slimming
campaign. Two passes are already done and define the method and the standard:
`git show c6167ac` (BACKLOG 661→456) and `git show 25bc0a5` (dead-ends registry,
73 entries dispositioned via a verified table). **The ratified principle: a note
earns deletion when its durable content is enforced in code or documented in an
operating doc with its mechanism and numbers — git keeps the full text of
everything removed. We can only document so much; what stays must be load-bearing.**

Scope: every `docs/*.md` deep-dive. NOT in scope (pointer fixes only):
`docs/dead-ends.md` (just cleaned), `docs/pipeline-wide-field-untracked.md`
(the operating walkthrough), `CLAUDE.md`, `README.md`, `TOOLS.md`, `MEMORY.md`,
`BACKLOG.md`. `docs/README.md` is in scope only as the index — it must match
your dispositions when you finish.

## Method (the proven shape — follow it)

1. **Inventory first.** `wc -l docs/*.md`; list every deep-dive with its size.
2. **Per file, decide a disposition with evidence:**
   - **RETIRE (delete)** — every durable finding has graduated (verify each
     claim in the file against TOOLS.md / dead-ends / the walkthrough / script
     docstrings: is the load-bearing fact recorded there?). If a unique
     load-bearing fact has NOT graduated, graduate it first (add the fact to
     the right operating doc, compactly) and only then retire the file.
     Strong candidates: the three drift-bannered files
     (`objective-qa-defect-metrics.md`, `plate-solving-and-drizzle.md`,
     `rc-astro-cli-linux.md` — their banners from `git show e40c007` say what
     drifted), and any file about tools/routes no longer in the toolkit.
   - **CONDENSE** — the file documents a live class or open investigation but
     carries superseded sections or narrative; compress to mechanism + numbers
     + scope, keeping its cited anchors.
   - **KEEP** — the file is the live deep record for an open thread (e.g. the
     one-sided band, lunar class facts, the wide-field-untracked registration
     deep-dive if still the "route + traps" reference the code cites).
3. **Citations are binding.** Before removing or renaming ANY file or section:
   `grep -rn "<filename>"` and grep its named topics across scripts/, web/,
   docs/, and the root .md files. A topic cited from live code or an operating
   doc must survive somewhere, and every pointer you break must be repointed in
   the same commit. Known live citations to respect:
   `docs/ui-position-and-zero-state-report.md` is cited from `web/serve.py` and
   `web/index.html` comments; `docs/wide-field-untracked-registration.md` from
   `README.md` and `CLAUDE.md`; `docs/lunar-lucky-imaging.md` from
   `run_lunar_pipeline.sh`, `TOOLS.md`, `BACKLOG.md`. Verify rather than trust
   this list — and treat any citation you find the same way.
4. **A reading is a hypothesis.** Verify "this graduated" by opening the
   operating doc and finding the fact, not by assuming. Where you verify a
   claim by running something, run read-only probes only — build nothing,
   process no pixels.
5. **Style for anything you write:** mechanism + numbers + scope; no
   chronological narrative, no session tags, no dates outside ratification
   stamps (CLAUDE.md binding rule).
6. **Commit as you go** in logical phases with evidence-bearing messages, each
   ending with the repo's Co-Authored-By line for your model. Leave the tree
   clean.

## Deliverable

`DOCS_CLEANUP_PROMPT_report.md` at the repo root (tracked, committed), holding:

1. The disposition table: file → lines before → RETIRED / CONDENSED (new size)
   / KEPT, with the one-line reason and, for every retirement, WHERE each
   unique load-bearing fact now lives (verified pointer).
2. Every graduation you performed (fact → operating doc it landed in).
3. Every citation you repointed (from → to).
4. Before/after totals for docs/.
5. Anything you could NOT settle, stated as a decision for the user with
   options — never silently skipped.
6. The verification evidence: the grep sweep showing no dangling references to
   removed files, and the docs/README.md index matching the surviving set.

The report will be audited by another session against your commits — write it
so that audit can re-run your checks from what you state.
