#!/usr/bin/env python3
"""PRODUCT-level no-regression guard for a linear stack — the check the repo did
not have when a 31x background regression shipped and stayed in for six days.

Usage:
  baseline_guard.py <session-dir> <set> <stack.fit> [--seed] [--note="why"]
  baseline_guard.py --baseline=<slot.json> <stack.fit> [--seed] [--reseed] [--note="why"]
                    [--coverage=<coverage.json> | --rect=x,y,w,h]   (a rect SOURCE, required to seed)
  baseline_guard.py --selftest        (data-free: the compare rule on planted measures,
                                       and the slot routing on a scratch tree)

  --seed   record the CURRENT measures as the set's baseline (first run, or after
           a human has ratified a deliberate change). Refuses to overwrite an
           existing baseline unless --reseed is also given.
  default  measure the stack, compare against datasets/<session>/<set>/baseline.json,
           print the table, exit 0 (PASS) or 1 (REGRESSION).
  --baseline=<path>  an EXPLICIT slot: read and write exactly that file, derive
           nothing from a session/set (the positional session and set are then
           OPTIONAL — the slot path is the identity, and the log line names it);
           the Siril scratch goes to <slot dir>/qa_work. --seed / --reseed / the
           ceiling / the level rows behave exactly as for a set.

THE CORPUS SLOT (datasets/corpus/baseline.json). The multi-night combine's product
has no set: run_corpus_combine.sh files its finish under the REFERENCE set, and
the per-set derivation would land the corpus baseline on that set's own
baseline.json — overwriting the set product's accepted measures with the
corpus's. The corpus is a first-class product and gets its own slot, the same
schema and contract block as the per-set files, written only by this script.
Two rules exist ONLY for an explicit slot (the per-set default path is untouched):
  ABSENT SLOT = FIRST BUILD. A compare against a missing explicit slot prints one
    line ("no corpus baseline ... first build; seed after the owner's acceptance")
    and exits 0 — a first build must never seed itself: the seed is the human's
    acceptance, not the chain's.
  THE RECTANGLE. A union's canvas has EMPTY corners (framing=max leaves
    uncovered triangles around the rotated members' quad), so the per-set
    canvas-edge corner regions measure the compose's pedestal there, not sky —
    MEASURED on the corpus: three of four canvas-edge corner boxes read a Green
    median of 6.1e-5 against 6.0e-4 of covered sky, and the first seed died on
    Siril's `Sigma: -nan` for a constant layer (regional_stat.py's docstring has
    the verbatim lines). An explicit slot therefore REQUIRES a rectangle source
    to SEED: --coverage=<coverage_frame.py record> (its `rect_siril_crop_args`,
    the largest fully covered axis-aligned rectangle at the record's own
    floor/channel/grid) or --rect=x,y,w,h (Siril crop convention); regional_stat
    places the five regions INSIDE it (corners `margin` in from its edges, centre
    at its centre). The seeded baseline RECORDS the rectangle and its provenance
    (the coverage record's path + head/tail sha, its source product + that
    product's stack_id, floor/channel/grid). On COMPARE the guard REUSES the
    stored rectangle and never recomputes it — a recomputed rectangle would move
    the boxes and compare unlike regions; a --coverage/--rect given on a compare
    is ignored with a printed note — and REFUSES loudly if the stored rectangle
    falls outside the new product's canvas (the regions could not be the same;
    re-seed on acceptance). corner_spread_pct / edge_dipole_x keep their meaning
    inside the rectangle. Per-set slots are untouched: canvas placement, as seeded.
  IDENTITY. The slot keys on the PRODUCT it was seeded from — the recorded
    `stack` path (its tag) with the seeded file's `stack_id` beside it. A
    differently-tagged product (a candidate or arm built with --out=<other tag>
    runs the same guard block) is reported as "different product — not compared",
    exit 0, never as a regression: it is not this slot's product. The path is the
    key rather than stack_id alone because every rebuild changes stack_id (the
    header carries PIPEREV), and the guard's whole purpose is to compare a
    rebuild against the accepted one.

WHY THIS EXISTS. Every guard the repo had before this one — check_bitdepth,
check_calibrate, check_stack_rejection — verifies WIRING: that the code is
plumbed the way doctrine says. None of them look at the product. `--desky` left
every wire intact and corrupted the data: corner spread went 0.4% -> 12.4% and
no guard fired. Worse, the change's own
validation suite could not see it, because a whole-frame plane fit CANCELS under
a partial sign inversion, so the defect's signature was read as proof of success.
The lesson is not "choose better metrics" — it is that a metric chosen by the
author of a change, run once at change time, is not a regression guard. A
regression guard compares TODAY'S PRODUCT to a RECORDED EARLIER ONE.

WHAT IT MEASURES (both are Siril's own `stat`, via scripts/qa/regional_stat.py —
this file runs no pixel maths, it drives the tool and compares recorded numbers):
  corner_spread_pct  max/min of the four corner medians, box 400 / margin 200.
                     The broad flatness figure. --desky: 0.4 -> 12.4.
  edge_dipole_x      ((TR+BR)-(TL+BL))/2 on corner medians normalised to their
                     own mean, box 80 / margin 2. 0 = left-right symmetric. This
                     is the term the earlier validation was blind to, because a
                     centre-vs-corner radial ratio averages the two sides
                     together and a whole-frame plane fit cancels them.
                     --desky: +0.004 -> +0.148.
  centre_median      per channel. Catches a level or channel-balance shift that
                     leaves the geometry alone.

WHAT IT IS NOT. It is NOT a quality gate and must never become one. It has no
opinion about whether a render is good — that judgement is the tools' measures
plus the user's eyes, per the review contract. It answers exactly one question:
"does this product still measure like the one a human accepted?" A deliberate
improvement FAILS it, and that is correct: the human re-seeds the baseline and
records why. Blocking on a self-derived quality threshold would be the FORBIDDEN
case in CLAUDE.md ("an in-house gate or audit that reads the render and blocks
it"); comparing against a human-ratified prior measurement is the no-regression
record the dataset model has always specified (datasets/README.md).

TOLERANCES live in the baseline file, not in this script, so they are visible
and ratifiable per dataset. Defaults on seed are deliberately loose enough to
pass ordinary run-to-run variation and tight enough that the --desky regression
trips them by more than an order of magnitude.

THE LEVEL MEASURE IS ADVISORY WHILE THE PRODUCT'S NORMALIZATION STATEMENT
DIFFERS FROM THE BASELINE'S. `centre_median_per_channel` was measured to move
+56% and -49% on UNCHANGED data under `-output_norm` (a global min-max rescale
keyed to one darkest pixel; docs/dead-ends/stacking-compose.md, the zero-point
entry), and a product built without it sits at its reference's own sky, ~x1.8
above a rescaled one — a level fail there says only that the anchor changed by
design (docs/dead-ends/stacking-compose.md, the zero-point entry). So the seed records the product's
STACKNRM header (absent = "addscale+output_norm", the pre-change default every
existing baseline and product share, which keeps the rule inert on them), and
the compare counts the centre-median rows as FAILS only when the two statements
are equal; when they differ the rows print as ADVISORY, not counted. Re-seeding
on acceptance records the new statement and re-arms the check. No threshold is
added: the rule is the equality of two recorded strings. corner_spread_pct and
edge_dipole_x are always hard — they are the structure measures.

THE ABSOLUTE CORNER-SPREAD CEILING WARNS; IT DOES NOT STOP (owner-directed).
`corner_spread_pct_max_abs` is the one threshold here that is SELF-DERIVED — it
compares the product to a number, not to a human-accepted prior measurement —
and the guard's own contract (above) is that it is a no-regression RECORD, never
a quality gate. It misfired on aug14/set-05: a Milky Way band across the frame
puts a true 4.38% corner spread on the product (left corners bright), the same
measure read 8.2% on that set's -output_norm product (never seeded), and the
guard cannot separate sky structure from a flat error (its register row calls
the corner measures self-fulfilling for flat contamination). So the ceiling is
a CROSSING warning: when the product exceeds it AND the accepted baseline did
not, the guard prints a CEILING block that tells the human to EXAMINE THE IMAGE
MANUALLY — the four corners at 1:1 on the 16-bit judge surface, the shape of
the background map (radial = flat/vignetting; a left-right or top-bottom slope
= sky or sky x V, compare readiness.json's flat-quality row; blocky =
coverage), and whether the field itself carries the gradient — and records the
verdict in the baseline note on the next seed (the seed itself prints the block
when it is taken over the ceiling). A product that stays over a ceiling its
accepted baseline already sat over prints nothing: that baseline was examined
at seed and carries the verdict, so the block would repeat on every run with no
new information — the decoration the acceptance-measures rule names
(owner-approved 2026-08-29, after aug14/set-05's seed at 4.381 made it print on
every run); growth beyond the baseline is the over-baseline rule's. The check
that carries the
--desky class (0.4% -> 12.4%) is the OVER-BASELINE rule (+1.0 over the accepted
product), which stays hard, as do the dipole cap and the level rows; the
--selftest keeps that case as the positive control. Exit stays 0 on a ceiling
warning alone: one product of seventeen needed the look, and the look takes a
moment.

REMOVAL CONDITION: retire when a tool reports a headless product-level
regression verdict against a stored reference. Nothing does today.
"""
import argparse
import hashlib
import json
from astropy.io import fits          # HEADER only (STACKNRM) — no pixel access
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGIONAL = os.path.join(REPO, "scripts", "qa", "regional_stat.py")

# Seed defaults. corner spread: absolute ceiling plus an allowance over baseline,
# so a set that legitimately sits at 0.9% is not held to a 0.4% set's number.
# The --desky regression measured 12.4% and +0.148 — both exceed these by >10x.
DEFAULT_TOL = {
    "corner_spread_pct_max_abs": 3.0,
    "corner_spread_pct_max_over_baseline": 1.0,
    "edge_dipole_x_max_abs": 0.050,
    "centre_median_max_frac_change": 0.25,
}
# The normalization statement a product or baseline carries when it has none:
# every pre-change stack and all 13 seeded baselines (flat_differential.py
# assumes the same default), so the advisory rule is inert on them.
DEFAULT_NRM = "addscale+output_norm"


def compare(now, b, tol):
    """The rule, PURE: (fails, advisories, ceiling) of the measured `now` against
    the baseline's measures `b` under `tol`. The four checks are the ones this
    guard always ran; the routing is (1) the centre-median loop, which appends
    to `advisories` instead of `fails` when the two normalization statements
    differ (docstring: THE LEVEL MEASURE IS ADVISORY ...), and (2) the absolute
    corner-spread ceiling, which appends to `ceiling` only on a CROSSING (product
    over it, baseline under it) — a warning to examine the image, never a fail
    (docstring: THE ABSOLUTE CORNER-SPREAD CEILING WARNS)."""
    spread, dip = now["corner_spread_pct"], now["edge_dipole_x"]
    chans = now["centre_median_per_channel"]
    fails, advisories, ceiling = [], [], []
    level = (fails if now.get("stacknrm", DEFAULT_NRM) == b.get("stacknrm", DEFAULT_NRM)
             else advisories)

    if (spread > tol["corner_spread_pct_max_abs"]
            and b["corner_spread_pct"] <= tol["corner_spread_pct_max_abs"]):
        ceiling.append(f"corner_spread_pct {spread} crosses the absolute ceiling "
                       f"{tol['corner_spread_pct_max_abs']} (the accepted baseline "
                       f"{b['corner_spread_pct']} was under it)")
    if spread - b["corner_spread_pct"] > tol["corner_spread_pct_max_over_baseline"]:
        fails.append(f"corner_spread_pct {spread} is "
                     f"{spread - b['corner_spread_pct']:+.3f} over baseline "
                     f"{b['corner_spread_pct']} (allowed "
                     f"+{tol['corner_spread_pct_max_over_baseline']})")
    if abs(dip) > tol["edge_dipole_x_max_abs"]:
        fails.append(f"edge_dipole_x {dip:+.4f} exceeds |{tol['edge_dipole_x_max_abs']}| "
                     "— a left-right edge asymmetry of this size is the --desky "
                     "signature (docs/dead-ends.md)")
    for ch, v in chans.items():
        bv = b["centre_median_per_channel"].get(ch)
        if bv and abs(v - bv) / bv > tol["centre_median_max_frac_change"]:
            level.append(f"centre {ch} {v:.1f} vs baseline {bv:.1f} "
                         f"({100*(v-bv)/bv:+.1f}%)")
    return fails, advisories, ceiling


def ceiling_block(spread, ceiling):
    """The owner-directed warning, printed wherever the ceiling is exceeded
    (compare and seed alike). Loud by design: it must not read as a pass."""
    return (f"\nCEILING — corner_spread_pct {spread} exceeds the absolute ceiling "
            f"{ceiling}: EXAMINE THE IMAGE MANUALLY before accepting this product "
            "(owner-directed):\n"
            "  (1) the four corners at 1:1 on the 16-bit judge surface;\n"
            "  (2) the background map's SHAPE — radial = flat/vignetting; a left-right\n"
            "      or top-bottom slope = sky or sky x V (compare the flat-quality row in\n"
            "      readiness.json); blocky = coverage;\n"
            "  (3) whether the field itself carries the gradient (a Milky Way band across\n"
            "      the frame is legitimate).\n"
            "  Record the verdict in the baseline note on the next seed. This measure\n"
            "  cannot separate sky structure from a flat error (its register row); it\n"
            "  warns, it does not stop.")


def selftest():
    """Data-free: the rule must go RED on a real level regression under a
    matching statement, stay quiet on ordinary variation, go ADVISORY (not RED)
    on a level move under a changed statement, and stay RED on structure
    regardless of the statement. Also: a baseline WITHOUT the field (all 13
    seeded today) behaves as the default statement."""
    base = {"corner_spread_pct": 0.7, "edge_dipole_x": 0.004,
            "centre_median_per_channel": {"ch0": 43.0, "ch1": 43.3, "ch2": 42.9},
            "stacknrm": DEFAULT_NRM}
    old_base = {k: v for k, v in base.items() if k != "stacknrm"}   # no field

    def now(level=1.0, spread=0.7, dip=0.004, nrm=DEFAULT_NRM):
        return {"corner_spread_pct": spread, "edge_dipole_x": dip,
                "centre_median_per_channel": {k: v * level for k, v in
                                              base["centre_median_per_channel"].items()},
                "stacknrm": nrm}
    hi_base = dict(base, corner_spread_pct=4.4)      # a seed taken over the ceiling (aug14/set-05: 4.381), examined at seed
    lo_base = dict(base, corner_spread_pct=0.4)      # the --desky class's accepted product (0.4%)
    mid_base = dict(base, corner_spread_pct=2.6)     # an accepted product under the ceiling
    cases = [  # (label, now, baseline, expected fails, advisory expected, ceiling expected)
        ("same STACKNRM, centre +30% -> RED",            now(1.30), base, 1 * 3, False, False),
        ("STACKNRM differs, centre +80% -> ADVISORY",   now(1.80, nrm="addscale"), base, 0, True, False),
        ("STACKNRM differs, corner_spread +2.0 -> RED", now(1.80, spread=2.7, nrm="addscale"), base, 1, True, False),
        ("same STACKNRM, centre +10% -> PASS",           now(1.10), base, 0, False, False),
        ("STACKNRM differs, edge_dipole +0.10 -> RED",  now(1.80, dip=0.104, nrm="addscale"), base, 1, True, False),
        ("baseline without the field, default product +30% -> RED", now(1.30), old_base, 3, False, False),
        ("baseline without the field, addscale product +80% -> ADVISORY", now(1.80, nrm="addscale"), old_base, 0, True, False),
        ("same STACKNRM, spread 4.9 vs baseline 4.4 (seeded over the ceiling) -> PASS, no ceiling", now(spread=4.9), hi_base, 0, False, False),
        ("spread 12.4 vs baseline 0.4 (--desky) -> RED via over-baseline, ceiling too (a crossing)", now(spread=12.4), lo_base, 1, False, True),
        ("spread 2.9 vs baseline 0.4 -> RED via over-baseline, no ceiling", now(spread=2.9), lo_base, 1, False, False),
        ("spread 3.5 vs baseline 2.6 -> PASS with CEILING warning (a crossing inside the +1.0 allowance)", now(spread=3.5), mid_base, 0, False, True),
    ]
    bad = 0
    for label, n, bl, nf, adv, ceil in cases:
        fails, advisories, ceiling = compare(n, bl, DEFAULT_TOL)
        ok = (len(fails) == nf) and (bool(advisories) == adv) and (bool(ceiling) == ceil)
        print(f"  selftest {'ok  ' if ok else 'WRONG'} [{len(fails)} fail, "
              f"{len(advisories)} advisory, {len(ceiling)} ceiling] {label}")
        bad |= not ok
    if bad:
        print("baseline_guard --selftest: FAIL — the rule does not fire as stated")
        return 1
    print("OK: baseline_guard compare rule — 11 cases: RED on level under a matching "
          "STACKNRM, ADVISORY under a differing one, RED on structure either way, "
          "PASS on ordinary variation, field-less baselines read as the default, "
          "the absolute ceiling WARNS on a crossing only (never fails; silent over a "
          "baseline already over it) while the --desky class still goes RED through "
          "the over-baseline rule")
    return selftest_slot(base, now)


def selftest_slot(base, now):
    """THE EXPLICIT SLOT, on a scratch tree under $HOME/.cache, no Siril: --baseline
    writes and reads ONLY the given path (a per-set baseline planted beside it is
    byte-identical after, and no datasets/<session>/<set> is created for the
    session/set the flag makes optional); an absent slot prints the first-build
    line and exits 0 (never seeds); a differently-tagged product is 'not compared'
    (exit 0, never a regression); seed / re-seed refusal / PASS / REGRESSION /
    ceiling all run through the flag with the same verdicts as a set."""
    import contextlib, io, shutil
    T = os.path.join(os.path.expanduser("~"), ".cache", "astro-imaging", "baseline_guard_selftest")
    shutil.rmtree(T, ignore_errors=True); os.makedirs(os.path.join(T, "sets", "set-01"))
    sibling = os.path.join(T, "sets", "set-01", "baseline.json")
    open(sibling, "w").write('{"planted": "per-set baseline beside the slot"}\n'); sib0 = open(sibling, "rb").read()
    slot = os.path.join(T, "corpus", "baseline.json")
    ghost = os.path.join(REPO, "datasets", "selftest-ghost")          # must never be created
    ident = dict(base, stack="web/results/x/stack_corpus_spcc.fit", stack_id="seedsha")
    def args(**kw):
        return parse_args(["--baseline=" + kw.pop("slot", slot), kw.pop("session", "selftest-ghost"),
                           kw.pop("set", "set-zz"), kw.pop("stack", "x.fit")] + [f"--{k}" if v is True else f"--{k}={v}" for k, v in kw.items()])
    def go(a, rec):
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                rc = run(rec, a, *resolve_slot(a)[::2])
        except SystemExit as e:
            rc = ("SystemExit", str(e))
        return rc, out.getvalue()
    bad = 0
    def check(label, ok, detail=""):
        nonlocal bad
        print(f"  selftest {'ok  ' if ok else 'WRONG'} {label} {detail}"); bad |= not ok
    rc, o = go(args(), ident)
    check("--baseline, absent slot, no --seed -> the first-build line, exit 0, nothing written",
          rc == 0 and "first build" in o and not os.path.exists(slot), f"rc={rc}")
    rc, o = go(args(seed=True, note="selftest seed"), ident)
    check("--baseline --seed -> writes ONLY the slot", rc == 0 and os.path.exists(slot) and json.load(open(slot))["measures"]["stack_id"] == "seedsha", f"rc={rc}")
    check("  the per-set baseline planted beside it is byte-identical", open(sibling, "rb").read() == sib0)
    check("  no datasets/<session>/<set> was derived for the optional session/set", not os.path.exists(ghost))
    rc, o = go(args(seed=True), ident)
    check("--baseline --seed again without --reseed -> REFUSED", isinstance(rc, tuple) and "exists" in rc[1], f"rc={rc}")
    rc, o = go(args(), dict(ident, stack_id="rebuild1"))
    check("--baseline, same product tag rebuilt, same measures -> PASS 0", rc == 0 and "PASS" in o, f"rc={rc}")
    rc, o = go(args(), dict(ident, stack_id="rebuild2", corner_spread_pct=2.7))
    check("--baseline, same tag, corner_spread +2.0 -> REGRESSION 1", rc == 1 and "REGRESSION" in o, f"rc={rc}")
    rc, o = go(args(), dict(ident, stack_id="rebuild3", corner_spread_pct=3.5))
    check("--baseline, same tag, spread 3.5 vs 0.7 -> RED over-baseline (+2.8) with the CEILING block", rc == 1 and "CEILING" in o, f"rc={rc}")
    rc, o = go(args(), dict(ident, stack="web/results/x/stack_candidate_spcc.fit", stack_id="cand", corner_spread_pct=9.9))
    check("--baseline, DIFFERENT product tag (a candidate/arm), even a wild measure -> 'not compared', exit 0", rc == 0 and "not compared" in o and "REGRESSION" not in o, f"rc={rc}")
    rc, o = go(args(reseed=True, note="accepted"), dict(ident, stack_id="accepted2"))
    check("--baseline --reseed -> replaces the slot", rc == 0 and json.load(open(slot))["measures"]["stack_id"] == "accepted2", f"rc={rc}")
    a = parse_args(["sessions/selftest-ghost", "set-zz", "x.fit"])
    check("default (no flag) still derives datasets/<session>/<set>/baseline.json (string only, nothing touched)",
          resolve_slot(a)[0] == os.path.join(REPO, "datasets", "selftest-ghost", "set-zz", "baseline.json") and not os.path.exists(ghost))
    # THE RECTANGLE rules (docstring), on the slot the flag cases seeded above
    def rr(a, canvas, seeding):
        try:
            return resolve_rect(a, slot, True, canvas, seeding)
        except SystemExit as e:
            return ("SystemExit", str(e))
    r = rr(args(seed=True), (1000, 800), True)
    check("explicit slot, --seed with NO rect source -> REFUSED, naming the coverage_frame.py command", isinstance(r, tuple) and r[0] == "SystemExit" and "coverage_frame.py" in r[1], str(r)[:90])
    r = rr(args(seed=True, rect="100,100,800,600"), (1000, 800), True)
    check("explicit slot, --seed --rect inside the canvas -> the rect and its placement", r == ([100, 100, 800, 600], {"source": "rect", "rect_siril_crop_args": [100, 100, 800, 600]}), str(r)[:90])
    r = rr(args(seed=True, rect="500,500,800,600"), (1000, 800), True)
    check("explicit slot, --seed --rect outside the canvas -> REFUSED", isinstance(r, tuple) and "does not fit" in r[1])
    go(args(reseed=True, note="with rect"), dict(ident, stack_id="withrect", placement={"source": "rect", "rect_siril_crop_args": [100, 100, 800, 600]}))
    r = rr(args(), (1000, 800), False)
    check("compare: the STORED rect is reused (never recomputed)", r[0] == [100, 100, 800, 600], str(r[0]))
    r = rr(args(coverage="/nonexistent/coverage.json"), (1000, 800), False)
    check("compare with --coverage given: ignored, the stored rect still reused", r[0] == [100, 100, 800, 600])
    r = rr(args(), (800, 600), False)
    check("compare on a product whose canvas cannot hold the stored rect -> REFUSED loudly", isinstance(r, tuple) and "REFUSED" in r[1] and "outside" in r[1], str(r)[:80])
    check("rect_fits_canvas: the corpus rect [852,445,6816,4578] fits 8520x5668 and not 8000x5000", rect_fits_canvas([852, 445, 6816, 4578], (8520, 5668)) and not rect_fits_canvas([852, 445, 6816, 4578], (8000, 5000)))
    shutil.rmtree(T, ignore_errors=True)
    if bad:
        print("baseline_guard --selftest: FAIL — the explicit-slot routing does not behave as stated")
        return 1
    print("OK: baseline_guard explicit slot — 18 cases: --baseline reads/writes only its path, "
          "the optional session/set derive nothing, an absent slot is a first build (exit 0, "
          "never seeded), a differently-tagged product is 'not compared' (exit 0), seed / "
          "re-seed refusal / PASS / REGRESSION / ceiling run through the flag as for a set, and "
          "THE RECTANGLE: a seed needs a rect source (refused with the coverage_frame command), "
          "a rect must fit the canvas, a compare reuses the stored rect (a passed source is ignored) "
          "and refuses when the stored rect falls outside the new canvas")
    return 0


def _measure(stack, workdir, tag, box, margin, rect=None):
    """Siril `stat` on five regions via regional_stat.py. Returns per-channel
    medians. The .ssf and Siril workdir land beside the record, which must be
    under $HOME — the Siril flatpak has a private /tmp. `rect` (Siril crop
    convention) places the regions inside a rectangle (docstring: THE RECTANGLE)."""
    out = os.path.join(workdir, f"baseline_{tag}.json")
    if os.path.exists(out):
        os.remove(out)          # never read a stale record if regional_stat refuses
    r = subprocess.run([sys.executable, REGIONAL, stack, out,
                        f"--box={box}", f"--margin={margin}"]
                       + ([f"--rect={','.join(str(int(v)) for v in rect)}"] if rect else []),
                       capture_output=True, text=True)
    if not os.path.exists(out):
        sys.exit(f"baseline_guard: regional_stat produced no record for {tag}\n"
                 f"{r.stdout}\n{r.stderr}")
    d = json.load(open(out))["regions"]
    ch = "ch1" if "ch1" in d["TL"] else "ch0"
    return {k: d[k][ch]["median"] for k in ("TL", "TR", "BL", "BR", "center")}, d


def _derive(corners, edge):
    """Derived summaries over the tool's numbers — the same class of arithmetic
    inspect_stage.py already does over Siril's regdata. No pixel is read here."""
    c = {k: corners[k] for k in ("TL", "TR", "BL", "BR")}
    spread = round(100 * (max(c.values()) / min(c.values()) - 1), 3)
    e = {k: edge[k] for k in ("TL", "TR", "BL", "BR")}
    mn = sum(e.values()) / 4
    n = {k: v / mn for k, v in e.items()}
    dip = round(((n["TR"] + n["BR"]) - (n["TL"] + n["BL"])) / 2, 4)
    return spread, dip


def _sha(path, blocks=64):
    """sha256 of the head+tail of the file plus its size — a cheap identity that
    changes whenever the product does, without hashing 200 MB every run."""
    h = hashlib.sha256()
    sz = os.path.getsize(path)
    h.update(str(sz).encode())
    with open(path, "rb") as fh:
        h.update(fh.read(blocks * 4096))
        if sz > blocks * 8192:
            fh.seek(-blocks * 4096, os.SEEK_END)
            h.update(fh.read())
    return h.hexdigest()[:32]


def parse_rect(s):
    try:
        x, y, w, h = (int(v) for v in s.split(","))
    except ValueError:
        sys.exit(f"baseline_guard: --rect wants x,y,w,h integers (got {s!r})")
    return [x, y, w, h]


def rect_fits_canvas(rect, canvas_wh):
    x, y, w, h = rect; W, H = canvas_wh
    return x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= W and y + h <= H


def coverage_placement(path, canvas_wh):
    """The rectangle + provenance from a coverage_frame.py record, for an explicit slot's seed."""
    rec = json.load(open(path))
    r = rec.get("rect_siril_crop_args")
    if not r:
        sys.exit(f"baseline_guard: {path} proposes no rectangle (rect_fits {rec.get('rect_fits')!r}) — "
                 "run coverage_frame.py with a floor that yields one")
    if [int(v) for v in rec.get("canvas_wh", [])] != [int(v) for v in canvas_wh]:
        sys.exit(f"baseline_guard: the coverage record's canvas {rec.get('canvas_wh')} is not this product's "
                 f"{list(canvas_wh)} — a rectangle from another canvas would place the regions elsewhere")
    src = rec.get("source")
    return [int(v) for v in r], {"source": "coverage", "rect_siril_crop_args": [int(v) for v in r], "rect_fits": rec.get("rect_fits"),
                                  "coverage_record": os.path.relpath(os.path.abspath(path), REPO), "coverage_record_sha": _sha(path),
                                  "coverage_source": src, "coverage_source_stack_id": (_sha(src) if src and os.path.exists(src) else None),
                                  "coverage_floor": rec.get("floor"), "coverage_channel": rec.get("channel"), "coverage_grid": rec.get("grid")}


def coverage_hint(stack):
    base = stack[:-9] + ".fit" if stack.endswith("_spcc.fit") else stack
    return (f"python3 scripts/qa/coverage_frame.py {base} {base[:-4]}_coverage.json --grid=40x26 --channel=Green "
            "--floor=<the sibling-class sky floor; the corpus's previous record used 27.15>   then seed with --coverage=<that json>")


def resolve_rect(a, bpath, explicit, canvas_wh, seeding):
    """(rect, placement) for this run — docstring: THE RECTANGLE. Per-set: none.
    Explicit slot, seeding: a rect source is REQUIRED (--coverage or --rect).
    Explicit slot, comparing: the baseline's STORED rectangle, reused, never
    recomputed; refused if it falls outside this product's canvas."""
    if not explicit:
        return None, None
    if seeding:
        if getattr(a, "coverage", "") and getattr(a, "rect", ""):
            sys.exit("baseline_guard: give --coverage OR --rect, not both")
        if getattr(a, "coverage", ""):
            rect, pl = coverage_placement(a.coverage, canvas_wh)
        elif getattr(a, "rect", ""):
            rect, pl = parse_rect(a.rect), {"source": "rect"}
            pl["rect_siril_crop_args"] = rect
        else:
            sys.exit("baseline_guard: REFUSED — an explicit slot needs a rectangle source to seed (a union canvas has "
                     "empty corners; docstring: THE RECTANGLE). Produce one:\n  " + coverage_hint(a.stack))
        if not rect_fits_canvas(rect, canvas_wh):
            sys.exit(f"baseline_guard: REFUSED — rect {rect} does not fit the {list(canvas_wh)} canvas")
        return rect, pl
    if not os.path.exists(bpath):
        return None, None                      # first build: run() prints the line; nothing is measured
    b = json.load(open(bpath))["measures"]
    pl = b.get("placement") or {}
    stored = pl.get("rect_siril_crop_args")
    if not stored:
        sys.exit(f"baseline_guard: REFUSED — the slot {bpath} was seeded without a rectangle; re-seed it with "
                 "--coverage on the accepted product (docstring: THE RECTANGLE)")
    if getattr(a, "coverage", "") or getattr(a, "rect", ""):
        print(f"note: --coverage/--rect ignored on a compare — the baseline's stored rect {stored} is reused so the "
              "same regions are compared")
    if not rect_fits_canvas(stored, canvas_wh):
        sys.exit(f"baseline_guard: REFUSED — the baseline's stored rect {stored} falls outside this product's canvas "
                 f"{list(canvas_wh)}: the regions cannot be the same ones; re-seed on acceptance with --reseed")
    return [int(v) for v in stored], pl


def resolve_slot(a):
    """The slot this run reads and writes: (bpath, work, label). Default: the per-set
    contract datasets/<session>/<set>/baseline.json with its qa_work beside it.
    --baseline=<path>: EXACTLY that file — nothing derived from a session or set,
    the scratch beside the slot, the label its repo-relative path."""
    if a.baseline:
        bpath = os.path.abspath(a.baseline)
        return bpath, os.path.join(os.path.dirname(bpath), "qa_work"), os.path.relpath(bpath, REPO)
    sess = os.path.basename(os.path.normpath(a.session))
    dsdir = os.path.join(REPO, "datasets", sess, a.set)
    return os.path.join(dsdir, "baseline.json"), os.path.join(dsdir, "qa_work"), f"{sess}/{a.set}"


def seed_hint(a, stack):
    return (f"{sys.argv[0]} --baseline={a.baseline} {stack}" if a.baseline
            else f"{sys.argv[0]} {a.session} {a.set} {stack}")


def run(now, a, bpath, label):
    """Seed or compare `now` (the measured record) against the slot. Pure of Siril,
    so the selftest can drive every branch on planted measures; the explicit-slot
    rules (docstring: THE CORPUS SLOT) live here."""
    explicit = bool(a.baseline)
    spread, dip, chans, nrm = (now["corner_spread_pct"], now["edge_dipole_x"],
                               now["centre_median_per_channel"], now["stacknrm"])
    if a.seed or a.reseed:
        if os.path.exists(bpath) and not a.reseed:
            sys.exit(f"baseline_guard: {bpath} exists — pass --reseed to replace "
                     "it, and say why in --note. Re-seeding is how a DELIBERATE "
                     "change is accepted; doing it to silence a failure is how "
                     "the guard becomes decoration.")
        rec = {"tool": "Siril stat via scripts/qa/regional_stat.py; this file "
                       "orchestrates and compares, it reads no pixel",
               "measures": now, "tolerances": DEFAULT_TOL,
               "note": a.note or "seeded without a note",
               "_contract": "A no-regression RECORD, not a quality gate. It asks "
                            "only whether the product still measures like the one "
                            "a human accepted. A deliberate improvement fails it; "
                            "re-seed with --reseed and a note."}
        os.makedirs(os.path.dirname(bpath), exist_ok=True)
        json.dump(rec, open(bpath, "w"), indent=1)
        print(f"seeded {bpath}")
        print(f"  corner_spread_pct {spread}   edge_dipole_x {dip:+.4f}")
        if spread > DEFAULT_TOL["corner_spread_pct_max_abs"]:
            print(ceiling_block(spread, DEFAULT_TOL["corner_spread_pct_max_abs"]))
        return 0

    if not os.path.exists(bpath):
        if explicit:
            # ABSENT SLOT = FIRST BUILD (docstring): report, never seed, exit 0.
            print(f"no corpus baseline at {label} — first build; seed after the owner's "
                  f"acceptance:\n  {seed_hint(a, now['stack'])} --seed --note='why'")
            return 0
        sys.exit(f"baseline_guard: no baseline at {bpath} — seed one with --seed "
                 "once a human has accepted this product.")
    base = json.load(open(bpath))
    b, tol = base["measures"], base.get("tolerances", DEFAULT_TOL)
    if explicit and b.get("stack") != now["stack"]:
        # IDENTITY (docstring): the slot keys on the product it was seeded from.
        print(f"baseline_guard {label}: different product — not compared. The slot was "
              f"seeded from {b.get('stack')} (stack_id {b.get('stack_id')}); this is "
              f"{now['stack']} (stack_id {now['stack_id']}). A differently-tagged build "
              "is not this slot's product; nothing is judged.")
        return 0
    fails, advisories, ceiling = compare(now, b, tol)

    print(f"baseline_guard {label}" + ("  (the seeded file itself: same stack_id)" if b.get("stack_id") == now["stack_id"] else "")
          + (f"  rect {b['placement']['rect_siril_crop_args']} (stored, reused)" if b.get("placement", {}).get("rect_siril_crop_args") else ""))
    print(f"  {'':22}{'now':>10}{'baseline':>12}")
    print(f"  {'corner_spread_pct':22}{spread:10.3f}{b['corner_spread_pct']:12.3f}")
    print(f"  {'edge_dipole_x':22}{dip:+10.4f}{b['edge_dipole_x']:+12.4f}")
    for ch, v in sorted(chans.items()):
        print(f"  {'centre_'+ch:22}{v:10.1f}"
              f"{b['centre_median_per_channel'].get(ch, float('nan')):12.1f}")
    print(f"  {'stacknrm':22}{nrm:>10}  {b.get('stacknrm', DEFAULT_NRM)}")
    if advisories:
        print(f"\nADVISORY — the level anchor changed by design (baseline STACKNRM "
              f"{b.get('stacknrm', DEFAULT_NRM)!r}, product {nrm!r}): the centre-median "
              "rows are shown, not counted; re-seed on acceptance to re-arm:")
        for f in advisories:
            print(f"  ~ {f}")
    if ceiling:
        print(ceiling_block(spread, tol["corner_spread_pct_max_abs"]))
    if fails:
        print("\nREGRESSION — this product no longer measures like the accepted one:")
        for f in fails:
            print(f"  - {f}")
        print("\nIf the change is DELIBERATE and a human has judged it better, re-seed:")
        print(f"  {seed_hint(a, now['stack'])} --reseed --note='...'")
        return 1
    tags = [t for t, on in (("advisory", advisories), ("ceiling warning", ceiling)) if on]
    print("\nPASS" + (f" (with {' + '.join(tags)})" if tags else ""))
    return 0


def parse_args(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="<session-dir> <set> <stack.fit>, or with --baseline: <stack.fit>")
    ap.add_argument("--baseline", default="", help="explicit slot (see THE CORPUS SLOT)")
    ap.add_argument("--coverage", default="", help="rect source for an explicit slot's seed: a coverage_frame.py record")
    ap.add_argument("--rect", default="", help="rect source for an explicit slot's seed: x,y,w,h (Siril crop convention)")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--reseed", action="store_true")
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    if a.baseline:
        if len(a.paths) not in (1, 3):
            ap.error("with --baseline give <stack.fit> (a session and set are optional)")
        a.session, a.set, a.stack = (a.paths[0], a.paths[1], a.paths[2]) if len(a.paths) == 3 else ("", "", a.paths[0])
    else:
        if len(a.paths) != 3:
            ap.error("<session-dir> <set> <stack.fit> are required without --baseline")
        a.session, a.set, a.stack = a.paths
    return a


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    a = parse_args(sys.argv[1:])
    bpath, work, label = resolve_slot(a)
    stack = os.path.abspath(a.stack)
    if not os.path.exists(stack):
        sys.exit(f"baseline_guard: no such stack: {stack}")
    explicit, seeding = bool(a.baseline), bool(a.seed or a.reseed)
    hdr = fits.getheader(stack)                                        # HEADER only
    canvas_wh = (int(hdr["NAXIS1"]), int(hdr["NAXIS2"]))
    if explicit and not seeding and not os.path.exists(bpath):
        # ABSENT SLOT = FIRST BUILD: report and stop BEFORE measuring (a canvas-edge
        # measurement of a union would refuse on its empty corners for nothing).
        print(f"no corpus baseline at {label} — first build; seed after the owner's acceptance:\n  "
              f"{seed_hint(a, os.path.relpath(stack, REPO))} --seed --coverage=<coverage record> --note='why'")
        return 0
    rect, placement = resolve_rect(a, bpath, explicit, canvas_wh, seeding)
    os.makedirs(work, exist_ok=True)

    corners, craw = _measure(stack, work, "corners", 400, 200, rect)
    edge, _ = _measure(stack, work, "edge", 80, 2, rect)
    spread, dip = _derive(corners, edge)
    chans = {k: v["median"] for k, v in craw["center"].items()}
    # the product's own normalization statement, header-only; absent = the
    # pre-change default (see DEFAULT_NRM)
    nrm = str(fits.getheader(stack).get("STACKNRM", DEFAULT_NRM))
    now = {"corner_spread_pct": spread, "edge_dipole_x": dip,
           "centre_median_per_channel": chans, "stacknrm": nrm,
           "stack": os.path.relpath(stack, REPO), "stack_id": _sha(stack), "canvas_wh": list(canvas_wh)}
    if placement:
        now["placement"] = placement
    return run(now, a, bpath, label)


if __name__ == "__main__":
    sys.exit(main())
