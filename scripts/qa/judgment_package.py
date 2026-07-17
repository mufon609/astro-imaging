#!/usr/bin/env python3
"""Assemble a user-judgment package from render FINALS — scripted, verified.

DORMANT PENDING THE X86 RENDER REBUILD: the objective-delta path reads a
`.metrics.json` sidecar that no current tool writes (the render layer that
will is a gap pending x86), so the delta table cannot populate yet; the
package/verify machinery itself is chain-independent and stands.

Usage: judgment_package.py <outdir> <label>=<final.png> [...]
           --question="what the judge is deciding"
           --inspection=<notes.md>
           [--control=<label>] [--reference=<label>=<path.jpg>] [--note=... ]

--control names the baseline candidate; the package embeds a measured
candidate-vs-control delta table on the objective gate/defect metrics with
a per-candidate objective WIN | NULL | needs-eyes verdict (auto-discovered
from the <final>.metrics.json sidecar starcomb writes with --lossless). A
WIN names the delta that earns it; needs-eyes = mixed or aesthetic (the
user's call on the finals) — no "fixed/final/matched/close" language. With
no --control the first candidate is the baseline.

The review contract (README): a judgment set is a folder of WHOLE-FRAME
LOSSLESS finals (PNG16 + PNG8) with clean names and a QUESTION.md — nothing
else. Hand-assembly has a measured failure mode (a package shipped the
STARLESS-layer PNG16 mislinked as the final for 3 of 4 candidates), so this
tool takes each candidate's 8-bit lossless PNG (the path starcomb prints),
derives its _16bit.png sibling, and VERIFIES the pair before linking:

- the path must be a .png and must not name a _starless layer (the gate
  input is never a judgment surface),
- both files of the pair must exist,
- the pair's geometry and bit depths must agree (PNG header check); the
  pixel-level identity check runs on the tool-readable lossless surface
  (Siril `savetif` + `tifffile`) when the rebuilt render chain lands.

--inspection is REQUIRED (README pre-handoff contract; measured failure:
two consecutive packages shipped defects — a faint-dust allocation gap,
then 1:1 coring mottle — that native-resolution inspection of the object /
sky / star regions would have caught before the user's eyes were spent on
them). It names a notes file recording the assembler's own 1:1 inspection
of every candidate (+ the like-scale reference comparison when the dataset
has an answer key); it is copied into the package as INSPECTION.md and
linked from QUESTION.md.

Candidates are hardlinked (copy fallback) as NN_<label>.png +
NN_<label>_16bit.png in argument order. --reference adds ONE third-party
comparison image, named with LOSSY in the filename (an author's finish is
whatever encoding they published; it is comparison-only, never a judgment
surface). QUESTION.md gets the question, the file list, and the --note
lines verbatim; the caller states gate numbers and caveats there.
"""
import json
import os
import shutil
import struct
import sys

import numpy as np

# objective gate/defect metrics for the candidate-vs-control delta table:
# (label, path-into-metrics, lower_is_better). Star BRIGHTNESS and the
# other aesthetic dimensions are deliberately excluded — the harness
# reports objective deltas + an objective WIN|NULL, never an aesthetic
# verdict (that stays the user's eyes on the finals).
CMP = [
    ("SLpass", ("qa_starless", "pass"), None),
    ("SLcolor", ("qa_starless", "color"), True),
    ("SLgrad", ("qa_starless", "grad"), True),
    ("SLblotch", ("qa_starless", "resid"), True),
    ("SLrings", ("qa_starless", "ring_l"), True),
    ("aura_lum", ("star_shells", "aura_lum"), True),
]


def load_metrics_sidecar(png8):
    """The <final>.metrics.json starcomb writes beside every --lossless
    final; None if absent (an externally-produced PNG has no sidecar)."""
    p = png8[:-4] + ".metrics.json"
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except (ValueError, OSError):
        return None


def _dig(met, path):
    v = met
    for k in path:
        if not isinstance(v, dict) or k not in v:
            return None
        v = v[k]
    return v


def objective_verdict(control, cand, eps=0.15):
    """Objective WIN | NULL | needs-eyes vs the control, on the gate/defect
    metrics only. WIN = a defect metric improved beyond eps with NONE
    worsened (or a gate FAIL->PASS with none worse); NULL = nothing moved
    beyond eps; needs-eyes = mixed (some better, some worse) or a gate
    PASS->FAIL — the honest split, because 'better on a mix' and every
    AESTHETIC change are the user's call on the finals, never the
    harness's. No 'fixed/final/matched/close' language anywhere: a result
    is a WIN with its named delta, a clean NULL, or needs-eyes."""
    better, worse, flip = [], [], None
    for name, path, lower in CMP:
        cv, dv = _dig(control, path), _dig(cand, path)
        if cv is None or dv is None:
            continue
        if lower is None:                        # the PASS flag
            if bool(cv) != bool(dv):
                flip = "PASS->FAIL" if cv and not dv else "FAIL->PASS"
            continue
        d = float(dv) - float(cv)
        if abs(d) < eps:
            continue
        improved = (d < 0) if lower else (d > 0)
        tag = f"{name} {float(cv):.1f}->{float(dv):.1f}"
        (better if improved else worse).append(tag)
    if flip == "PASS->FAIL":
        return "needs-eyes", "gate PASS->FAIL" + (
            "; worse " + ", ".join(worse) if worse else "")
    if better and not worse:
        pfx = "gate FAIL->PASS, " if flip == "FAIL->PASS" else ""
        return "WIN", pfx + ", ".join(better) + " (none worse)"
    if not better and not worse and not flip:
        return "NULL", f"no gate/defect metric moved > {eps:g}"
    if flip == "FAIL->PASS" and not worse:
        return "WIN", "gate FAIL->PASS (none worse)"
    return "needs-eyes", ("mixed: better [" + ", ".join(better)
                          + "] worse [" + ", ".join(worse) + "]")


def png_ihdr(path):
    """IHDR inspection only (width, height, depth, color type) — a header
    read, not a decode. Pixel-level pair verification is a tool's job: the
    rebuilt finals surface reads Siril `savetif` output with `tifffile`
    (the in-house PNG decoder this replaced is retired — removal-condition
    register)."""
    with open(path, "rb") as f:
        head = f.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit(f"judgment_package: {path} is not a PNG")
    w, h, depth, ct = struct.unpack(">IIBB", head[16:26])
    return w, h, depth, ct


def verify_pair(png8, png16, step=16):
    """The final pair must be the SAME render. Geometry + bit-depth are
    verified from the PNG headers; the pixel-level identity check runs on
    the tool-readable lossless surface (Siril `savetif` + `tifffile`) when
    the rebuilt render chain lands — this tool is dormant until then (its
    metrics sidecar producer is also pending)."""
    w8, h8, d8, ct8 = png_ihdr(png8)
    w16, h16, d16, ct16 = png_ihdr(png16)
    if (w8, h8) != (w16, h16):
        sys.exit(f"judgment_package: {os.path.basename(png8)} and its "
                 f"_16bit sibling differ in geometry {(w8, h8)} vs "
                 f"{(w16, h16)}")
    if d16 != 16 or ct16 != 2:
        sys.exit(f"judgment_package: {png16} is not a 16-bit RGB PNG "
                 f"(depth {d16}, color type {ct16})")
    if d8 != 8:
        sys.exit(f"judgment_package: {png8} is not the 8-bit sibling "
                 f"(depth {d8})")


def place(src, dst):
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    notes = [a[7:] for a in sys.argv[1:] if a.startswith("--note=")]
    question = next((a[11:] for a in sys.argv[1:]
                     if a.startswith("--question=")), None)
    reference = next((a[12:] for a in sys.argv[1:]
                      if a.startswith("--reference=")), None)
    inspection = next((a[13:] for a in sys.argv[1:]
                       if a.startswith("--inspection=")), None)
    control = next((a[10:] for a in sys.argv[1:]
                    if a.startswith("--control=")), None)
    if len(args) < 2 or not question:
        sys.exit(__doc__)
    if not inspection:
        sys.exit("judgment_package: --inspection=<notes.md> is required — "
                 "the README pre-handoff contract: the assembler inspects "
                 "every candidate at native 1:1 (object / sky / stars, "
                 "whole frame at fit, like-scale reference comparison when "
                 "an answer key exists) and records what they see BEFORE "
                 "the user's eyes are asked for")
    if not os.path.exists(inspection):
        sys.exit(f"judgment_package: inspection notes {inspection} missing")
    if os.path.getsize(inspection) < 200:
        sys.exit(f"judgment_package: inspection notes {inspection} are "
                 "under 200 bytes — a real 1:1 inspection of every "
                 "candidate says more than that")
    outdir, cands = args[0], args[1:]
    if os.path.isdir(outdir) and os.listdir(outdir):
        sys.exit(f"judgment_package: {outdir} exists and is not empty — "
                 "a judgment set is assembled once, never edited in place")
    os.makedirs(outdir, exist_ok=True)

    lines = [f"# Judgment: {question}", "",
             "Open each file independently, full frame, your own viewers.",
             "_16bit.png = the float render at 65536 levels; .png = 8-bit",
             "lossless. All pipeline candidates are whole-frame lossless",
             "finals (verified pairs).", ""]
    metas, order = {}, []
    for i, spec in enumerate(cands, 1):
        if "=" not in spec:
            sys.exit(f"judgment_package: candidate {spec!r} is not "
                     "label=<final.png>")
        label, png8 = spec.split("=", 1)
        if not png8.endswith(".png") or png8.endswith("_16bit.png"):
            sys.exit(f"judgment_package: {png8} — pass the 8-bit lossless "
                     ".png final (the path starcomb prints); the _16bit "
                     "sibling is derived")
        if "_starless" in os.path.basename(png8):
            sys.exit(f"judgment_package: {png8} is a STARLESS layer — the "
                     "gate input is never a judgment surface; pass the "
                     "combined final")
        png16 = png8[:-4] + "_16bit.png"
        for p in (png8, png16):
            if not os.path.exists(p):
                sys.exit(f"judgment_package: missing {p}")
        verify_pair(png8, png16)
        d8 = os.path.join(outdir, f"{i:02d}_{label}.png")
        d16 = os.path.join(outdir, f"{i:02d}_{label}_16bit.png")
        place(png8, d8)
        place(png16, d16)
        metas[label], order = load_metrics_sidecar(png8), order + [label]
        print(f"[judgment_package] {i:02d}_{label}: verified pair linked"
              + ("" if metas[label] else " (no metrics sidecar)"))
        lines.append(f"- {i:02d}_{label}: FILL IN (knobs / what changed)")

    # measured candidate-vs-control deltas + objective WIN|NULL (Part 1
    # honest-comparison contract): each result is reported as an objective
    # WIN with its named delta, a clean NULL, or needs-eyes — never with
    # 'fixed/final/matched/close' language. Aesthetics stay the user's eyes.
    ctrl = control or order[0]
    if control and control not in order:
        sys.exit(f"judgment_package: --control={control} is not among the "
                 f"candidates {order}")
    if metas.get(ctrl) and any(metas.values()):
        lines += ["", f"## Objective deltas vs control ({ctrl})", "",
                  "Gate/defect metrics only (lower is better; SLpass is the "
                  "gate). WIN = a defect metric improved with none worse; "
                  "NULL = nothing moved; needs-eyes = mixed or aesthetic "
                  "(your call on the finals — the harness never judges the "
                  "look).", "",
                  "| candidate | verdict | measured detail |",
                  "|---|---|---|"]
        for lab in order:
            m = metas.get(lab)
            if m is None:
                lines.append(f"| {lab} | — | no metrics sidecar |")
            elif lab == ctrl:
                sl = m.get("qa_starless", {})

                def _r(k):
                    v = sl.get(k)
                    return f"{v:.1f}" if isinstance(v, (int, float)) else "?"
                lines.append(
                    f"| {lab} | (control) | SLcolor {_r('color')} grad "
                    f"{_r('grad')} blotch {_r('resid')} rings {_r('ring_l')} "
                    f"| ")
            else:
                verdict, detail = objective_verdict(metas[ctrl], m)
                lines.append(f"| {lab} | **{verdict}** | {detail} |")
    else:
        lines += ["", "_(no metrics sidecars found — objective deltas "
                  "unavailable; pass finals starcomb wrote with --lossless)_"]
    if reference:
        rl, rp = reference.split("=", 1)
        ext = os.path.splitext(rp)[1].lower() or ".jpg"
        dn = f"{len(cands) + 1:02d}_{rl}_LOSSY_ORIGINAL{ext}"
        place(rp, os.path.join(outdir, dn))
        print(f"[judgment_package] {dn}: reference (comparison only)")
        lines.append(f"- {dn}: third-party reference — LOSSY original, "
                     "comparison only, never a judgment surface")
    shutil.copy2(inspection, os.path.join(outdir, "INSPECTION.md"))
    lines.append("")
    lines.append("- INSPECTION.md: the assembler's own 1:1 pre-handoff "
                 "inspection of every candidate (README contract) — what "
                 "was seen, including known defects, before handover")
    lines += notes
    lines += ["", "Say which candidate pins (or what to ladder next)."]
    with open(os.path.join(outdir, "QUESTION.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[judgment_package] wrote {outdir}/QUESTION.md — fill in the "
          "candidate descriptions + gate numbers before handing it over")


if __name__ == "__main__":
    main()
