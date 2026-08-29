#!/usr/bin/env python3
"""THE POINTER GUARD — every pointer in the repo's Markdown must resolve.

    scripts/qa/check_doc_pointers.py              check every tracked or new .md
    scripts/qa/check_doc_pointers.py --selftest   prove it can go RED
    scripts/qa/check_doc_pointers.py --root DIR   check another tree

THREE CLASSES OF POINTER, three checks:
  1. a backticked REPO PATH (`scripts/qa/run_guards.sh`, `docs/dead-ends/`,
     `datasets/corpus/README.md`) must exist in the working tree;
  2. a BACKLOG slug reference (the BACKLOG:`slug` and BACKLOG `slug` forms)
     must have a `## `slug`` heading in BACKLOG.md — slugs replaced item
     numbers precisely because a dead one is greppable; this is that grep, run
     every time instead of when somebody remembers;
  3. a relative Markdown link ([text](path#anchor)) must resolve from the file
     that carries it.

WHY THIS EXISTS. A documentation audit found two slugs referenced from three
files with no BACKLOG section, one broken relative link in a read-order
registry file, records citing files deleted at a session reset as if present,
and a research document citing a retired prompt as a live path. Every one was
found by a human reading; nothing re-checked them, and a pointer rots silently
the first time its target moves. The guard suite verified WIRING in code and,
until `check_removal_conditions`, nothing in `.md` at all; this opens the
second `.md` invariant.

STANDARDS-FIRST. Class 3 is what markdown-link-check / lychee do; this
implements the same test rather than installing one (no network, one file, and
the repo's own file discovery). Classes 1 and 2 are this repo's citation
conventions — a backticked path IS a citation here, and slugs ARE the queue's
keys — and no off-the-shelf checker knows them. DOCTRINE, not measured.

WHAT IS SCANNED. Every .md that git tracks OR that is new and not ignored
(`git ls-files --cached --others --exclude-standard`), so a document is checked
BEFORE its first commit; outside a git tree, every .md under --root.

EXEMPTIONS — each a rule, never a list of files:
  (a) a path under a gitignored DATA ROOT (`sessions/`, `web/results/`): never
      present in a clone by design — counted, not checked;
  (b) a placeholder: a token carrying `<...>`, `$`, `[`, `]`, `|`, `…` or
      `...` names a shape, not a file;
  (c) a retired-by-commit citation: the `<sha>:<path>` form after `git show`
      is a history pointer, not a working-tree path. A bare basename in the
      same sentence is NOT exempt — write the sha form, or it is dead;
  (d) a bare name without `/` (`run_set_chain.sh`, `LICENSE.md`,
      `00-registry-contract.md` in the registry index whose link beside it IS
      checked) is a NAME, not a path, and is not checked — write the repo path
      to have it checked. Measured on the first real run: checking bare `.md`
      names by location flagged 19 correct citations (the index's 17 rows, a
      link's display text, an upstream repo's licence) and no true defect.
A brace group `{a, b}` is expanded (spaces inside the braces are the author's
formatting, not word breaks) and every alternative must exist; a glob (`*`,
`?`) must match at least one path. A token with whitespace is otherwise a
command line and each of its words is judged on its own.

NOT COVERED. Whether a target says what the citation claims; section anchors
inside a file; a path written in prose without backticks; a slug referenced
without the BACKLOG prefix. Reads Markdown only — touches no pixel, gates no
product, writes nothing: a QA tool outside the pipeline, so it carries no
`removal condition` — there is nothing for a tool to retire it into.
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile

TOP = ("scripts", "docs", "datasets", "web", "sessions")
DATA_ROOTS = ("sessions/", "web/results/")
BT = re.compile(r"`([^`\n]+)`")
LINK = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")
SLUG = re.compile(r"BACKLOG[: ]*`([a-z0-9][a-z0-9-]*)`")
HEAD = re.compile(r"^## `([a-z0-9][a-z0-9-]*)`", re.M)
PLACEHOLDER = re.compile(r"[<>$\[\]|…]|\.\.\.")
SHAPATH = re.compile(r"^[0-9a-f]{7,40}:")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def md_files(root):
    """Tracked + new-and-not-ignored .md via git; every .md by walk otherwise."""
    try:
        out = subprocess.run(
            ["git", "-C", root, "ls-files", "-z", "--cached", "--others",
             "--exclude-standard", "--", "*.md"],
            capture_output=True, check=True).stdout.decode()
        files = sorted(f for f in out.split("\0") if f)
        if files:
            return files
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    files = []
    for d, _, fs in os.walk(root):
        for f in fs:
            if f.endswith(".md"):
                files.append(os.path.relpath(os.path.join(d, f), root))
    return sorted(files)


def expand_braces(t):
    m = re.search(r"\{([^{}]*)\}", t)
    if not m:
        return [t]
    pre, post = t[:m.start()], t[m.end():]
    out = []
    for alt in m.group(1).split(","):
        out.extend(expand_braces(pre + alt.strip() + post))
    return out


def classify(word):
    """One word of a backticked token -> ('check'|'check-bare'|'exempt'|'skip', path)."""
    w = word.strip().strip("'\"").rstrip(",;:)")
    w = re.sub(r":\d+(-\d+)?$", "", w)          # a :LINE reference
    if w.startswith("./"):
        w = w[2:]
    if SHAPATH.match(w):                          # (c) <sha>:<path>
        return "exempt", w
    if "/" in w:
        first = w.split("/", 1)[0]
        if first not in TOP:
            return "skip", w
        if w.startswith(DATA_ROOTS):              # (a) gitignored data root
            return "exempt", w
        if PLACEHOLDER.search(w):                 # (b) a shape, not a file
            return "skip", w
        return "check", w
    return "skip", w                              # (d) a bare name is not a path


def exists_under(root, rel):
    rel = rel.rstrip("/")
    if any(c in rel for c in "*?"):
        return bool(glob.glob(os.path.join(root, rel), recursive=True))
    return os.path.lexists(os.path.join(root, rel))


def scan(root):
    """-> (findings, stats). A finding is (file, line, kind, token, why)."""
    findings = []
    stats = {"files": 0, "paths": 0, "exempt": 0, "slugs": 0, "links": 0}
    backlog = os.path.join(root, "BACKLOG.md")
    slugs = set(HEAD.findall(open(backlog, encoding="utf-8").read())) \
        if os.path.exists(backlog) else set()
    for rel in md_files(root):
        stats["files"] += 1
        fdir = os.path.dirname(rel)
        text = open(os.path.join(root, rel), encoding="utf-8").read()
        for lno, line in enumerate(text.split("\n"), 1):
            for tok in BT.findall(line):
                tok = re.sub(r"\{[^{}]*\}", lambda m: m.group(0).replace(" ", ""), tok)
                for word in tok.split():
                    kind, w = classify(word)
                    if kind == "skip":
                        continue
                    if kind == "exempt":
                        stats["exempt"] += 1
                        continue
                    stats["paths"] += 1
                    for alt in expand_braces(w):
                        if not exists_under(root, alt):
                            findings.append((rel, lno, "path", alt, "no such path"))
            for slug in SLUG.findall(line):
                stats["slugs"] += 1
                if slug not in slugs:
                    findings.append((rel, lno, "slug", slug,
                                     "no `## `%s`` heading in BACKLOG.md" % slug))
            for target in LINK.findall(line):
                if SCHEME.match(target) or target.startswith("#"):
                    continue
                stats["links"] += 1
                path = target.split("#", 1)[0]
                if not path:
                    continue
                full = os.path.normpath(os.path.join(root, fdir, path))
                if not os.path.lexists(full):
                    findings.append((rel, lno, "link", target,
                                     "resolves to %s, which does not exist"
                                     % os.path.relpath(full, root)))
    return findings, stats


def report(root):
    findings, st = scan(root)
    for f, lno, kind, tok, why in findings:
        print("  DEAD  %s:%d  %-5s %s  (%s)" % (f, lno, kind, tok, why))
    summary = ("%d files: %d repo paths + %d exempt, %d BACKLOG slugs, %d relative links"
               % (st["files"], st["paths"], st["exempt"], st["slugs"], st["links"]))
    if findings:
        print("\ncheck_doc_pointers: RED — %d dead pointer(s) over %s." % (len(findings), summary))
        print("  Fix the pointer (move it, cite by commit in the `git show <sha>:<path>`")
        print("  form, or name the slug that survives); never silence it with an exemption.")
        return 1
    print("OK: every pointer resolves — %s." % summary)
    print("    Scope: existence only. Not checked: whether a target says what the")
    print("    citation claims, section anchors, prose paths without backticks,")
    print("    slugs written without the BACKLOG prefix.")
    return 0


def selftest():
    """POSITIVE CONTROL (CLAUDE.md): a guard nobody has seen go RED is decoration.
    Plants one dead pointer of each class beside every exempt form, asserts the
    three fire and nothing else does, then removes them and asserts GREEN."""
    base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    os.makedirs(base, exist_ok=True)
    fix = tempfile.mkdtemp(prefix="check_doc_pointers.", dir=base)
    fail = 0
    try:
        for d in ("scripts", "docs", "datasets/x"):
            os.makedirs(os.path.join(fix, d))
        open(os.path.join(fix, "scripts/x.sh"), "w").write("#!/bin/sh\n")
        for n in ("a.json", "b.json"):
            open(os.path.join(fix, "datasets/x", n), "w").write("{}\n")
        open(os.path.join(fix, "BACKLOG.md"), "w").write(
            "# BACKLOG\n\n## `real-slug` — an item\n\ntext\n")
        good = (
            "Good: `scripts/x.sh`, `scripts/x.sh --flag <arg>`, BACKLOG:`real-slug`, "
            "BACKLOG `real-slug`, [link](../scripts/x.sh), [self](a.md), `docs/a.md`, "
            "`datasets/x/{a, b}.json`, `datasets/x/*.json`, `docs/`.\n"
            "Exempt: `sessions/aug09/work/flatdiff/arm_{A,B}.fit`, `web/results/x/stack_1.fit`, "
            "`datasets/<session>/<set>/recipe.json`, `git show abc1234:GONE_report.md`, "
            "`some_tool.sh`, `LICENSE.md`, `qa_work/*.json`, [web](https://example.org/x), [anchor](#here).\n")
        dead = "Dead: `scripts/gone.sh`, BACKLOG:`no-such-slug`, [dead](gone.md).\n"
        amd = os.path.join(fix, "docs/a.md")
        open(amd, "w").write(good + dead)

        # the planted dead path must NOT be in an exempt class (the director's condition)
        kind, _ = classify("scripts/gone.sh")
        if kind != "check":
            print("  *** FAIL *** the planted dead path classifies as %r, not 'check'" % kind); fail = 1
        else:
            print("  PASS  the planted dead path `scripts/gone.sh` is a checked class, not an exempt one")
        # the exempt data-root path is genuinely absent, so only the exemption can silence it
        if os.path.exists(os.path.join(fix, "sessions")):
            print("  *** FAIL *** fixture has a sessions/ dir; the exemption test is vacuous"); fail = 1

        # (1) RED — exactly the three planted pointers fire, one per class
        f1, st = scan(fix)
        kinds = sorted(k for _, _, k, _, _ in f1)
        toks = [t for _, _, _, t, _ in f1]
        want = ["link", "path", "slug"]
        if kinds != want or not ({"scripts/gone.sh", "no-such-slug", "gone.md"} <= set(toks)):
            print("  *** FAIL *** expected one dead pointer per class, got %r" % f1); fail = 1
        else:
            print("  PASS  a dead path, a dead slug and a dead link each go RED (%d of %d paths, %d slugs, %d links)"
                  % (len(f1), st["paths"], st["slugs"], st["links"]))
        for must_not in ("arm_", "web/results", "GONE_report", "some_tool", "LICENSE", "qa_work", "example.org"):
            if any(must_not in t for t in toks):
                print("  *** FAIL *** an exempt form was reported: %s" % must_not); fail = 1
        if st["exempt"] < 3:
            print("  *** FAIL *** exempt forms were not counted (%d)" % st["exempt"]); fail = 1
        else:
            print("  PASS  the data-root, placeholder, sha:path, bare-name and non-repo glob forms stay silent (%d exempt counted)" % st["exempt"])

        # (2) GREEN — remove the planted line and the same fixture passes
        open(amd, "w").write(good)
        f2, _ = scan(fix)
        if f2:
            print("  *** FAIL *** the clean fixture still reports %r" % f2); fail = 1
        else:
            print("  PASS  removing the planted pointers turns it GREEN")

        # (3) discovery — inside a git tree an UNCOMMITTED .md is still scanned
        subprocess.run(["git", "init", "-q", fix], check=True, capture_output=True)
        found = md_files(fix)
        if "docs/a.md" not in found or "BACKLOG.md" not in found:
            print("  *** FAIL *** git-mode discovery missed an untracked .md: %r" % found); fail = 1
        else:
            print("  PASS  git-mode discovery scans a new, uncommitted .md (%d files)" % len(found))
    finally:
        shutil.rmtree(fix, ignore_errors=True)
    if fail:
        return 1
    print("SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else report(a.root))
