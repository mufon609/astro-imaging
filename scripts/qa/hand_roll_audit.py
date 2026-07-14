#!/usr/bin/env python3
"""Standing guard for the orchestrate-not-hand-roll rule (CLAUDE.md).

The pipeline's job is to ORCHESTRATE + MEASURE industry-standard tools
(Siril / GraXpert / StarNet / astrometry.net, or a reference author's own
open tool) — never to reimplement the image PROCESSING in numpy. The bright
line is processing vs examining: examining numpy (metrics, gate, masks,
inspection rendering) is what the pipeline is FOR; processing numpy (code
that rewrites the deliverable's pixels — a stretch, denoise, colour
transform, saturation, SCNR, combine) must drive a real tool, unless no
available tool provides the mechanism on this rig and that is documented as
a sanctioned alternative with a removal condition (the StarNet-aarch64 /
DNG / astrometry.net precedent).

scripts/render/operators.json is the honest catalog of the chain's
processing operators. This audit enforces it:

- FAIL: a processing entry is incoherent (status 'tool' with no tool,
  'sanctioned' with no reason+removal_condition, 'migration-candidate' with
  no named tool it duplicates).
- FAIL: a top-level function in the product chain (starcomb.py) that is
  neither registered nor on the orchestration allowlist AND reads as a
  processing algorithm (the guard against the next throwaway hand-roll).
- WARN: a migration-candidate — numpy today, an available tool should do it
  (tracked, measured follow-on; not a silent violation).

Run standalone (exit nonzero on any FAIL) or import audit(). Wired into the
no-regression sweep so every build re-checks the rule.
"""
import ast
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTRY = os.path.join(REPO, "scripts", "render", "operators.json")

# tokens that mark a hand-rolled PROCESSING algorithm (a function that
# transforms image pixels), used only to flag UNREGISTERED, non-allowlisted
# chain functions — the tripwire for a new hand-roll
PROC_TOKENS = ("gaussian_filter", "rgb_to_lch", "lch_to_rgb", ".mtf(",
               "scnr", "huerot", "satgamma", "ppgamma", "chroma_core",
               "lum_core", "perline")


def _load():
    if not os.path.exists(REGISTRY):
        sys.exit(f"hand_roll_audit: no registry at {REGISTRY} — it is a "
                 "tracked file (the processing-operator catalog)")
    return json.load(open(REGISTRY))


def _check_registry(reg):
    """Coherence of every processing entry (the FAIL conditions)."""
    fails = []
    for op in reg.get("operators", []):
        name, kind = op.get("name", "?"), op.get("kind")
        if kind == "glue":
            continue
        if kind != "processing":
            fails.append(f"{name}: kind {kind!r} — must be 'processing' or "
                         "'glue'")
            continue
        st = op.get("status")
        if st == "tool":
            if not op.get("tool"):
                fails.append(f"{name}: status 'tool' but names no tool")
        elif st == "sanctioned":
            if not (op.get("reason") and op.get("removal_condition")):
                fails.append(f"{name}: status 'sanctioned' needs BOTH a "
                             "reason and a removal_condition (why no tool "
                             "provides it + when it retires)")
        elif st == "migration-candidate":
            if not op.get("duplicates"):
                fails.append(f"{name}: status 'migration-candidate' must "
                             "name the available tool it duplicates")
        else:
            fails.append(f"{name}: unknown status {st!r} (tool | sanctioned "
                         "| migration-candidate)")
    return fails


def _check_chain(reg):
    """Any top-level chain function that is neither registered nor
    allowlisted AND looks like a processing algorithm (the guard against a
    new hand-roll being added without classifying it)."""
    chain = os.path.join(REPO, reg["chain_file"])
    known = set(reg.get("orchestration_allowlist", []))
    for op in reg.get("operators", []):
        f = op.get("func", "")
        if f and ":" not in f and "(" not in f:   # a real function name
            known.add(f)
    src = open(chain).read()
    tree = ast.parse(src)
    fails = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name in known:
            continue
        body = ast.get_source_segment(src, node) or ""
        hits = [t for t in PROC_TOKENS if t in body]
        if hits:
            fails.append(f"{node.name} (line {node.lineno}): unregistered "
                         f"function reads as processing ({', '.join(hits)}) "
                         "— classify it in scripts/render/operators.json "
                         "(processing with a tool/reason, or glue) or move "
                         "the processing to a real tool")
    return fails


def audit(verbose=True):
    """Returns (ok, fails, warns). ok is False on any FAIL."""
    reg = _load()
    fails = _check_registry(reg) + _check_chain(reg)
    warns, tool, sanctioned = [], [], []
    for op in reg.get("operators", []):
        if op.get("kind") != "processing":
            continue
        st = op.get("status")
        if st == "migration-candidate":
            warns.append(f"{op['name']}: numpy — duplicates "
                         f"{op.get('duplicates')} (migrate: "
                         f"{op.get('backlog') or 'BACKLOG'})")
        elif st == "tool":
            tool.append(f"{op['name']} -> {op.get('tool')}")
        elif st == "sanctioned":
            sanctioned.append(f"{op['name']}: {op.get('removal_condition')}")
    if verbose:
        print(f"[hand-roll audit] {REGISTRY}")
        if tool:
            print("  DRIVES A TOOL (the goal):")
            for x in tool:
                print(f"    - {x}")
        if sanctioned:
            print("  SANCTIONED numpy (no tool provides it; removal "
                  "condition):")
            for x in sanctioned:
                print(f"    - {x}")
        for w in warns:
            print(f"  WARN migration-candidate: {w}")
        for f in fails:
            print(f"  FAIL: {f}")
        print(f"[hand-roll audit] {'PASS' if not fails else 'FAIL'} "
              f"({len(tool)} tool, {len(sanctioned)} sanctioned, "
              f"{len(warns)} to migrate, {len(fails)} fail)")
    return (not fails), fails, warns


if __name__ == "__main__":
    ok, _, _ = audit()
    sys.exit(0 if ok else 1)
