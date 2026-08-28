#!/usr/bin/env python3
"""PRODUCT-level no-regression guard for a linear stack — the check the repo did
not have when a 31x background regression shipped and stayed in for six days.

Usage:
  baseline_guard.py <session-dir> <set> <stack.fit> [--seed] [--note="why"]
  baseline_guard.py --selftest        (data-free: the compare rule on planted measures)

  --seed   record the CURRENT measures as the set's baseline (first run, or after
           a human has ratified a deliberate change). Refuses to overwrite an
           existing baseline unless --reseed is also given.
  default  measure the stack, compare against datasets/<session>/<set>/baseline.json,
           print the table, exit 0 (PASS) or 1 (REGRESSION).

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
design (BACKLOG:output-norm-zero-point). So the seed records the product's
STACKNRM header (absent = "addscale+output_norm", the pre-change default every
existing baseline and product share, which keeps the rule inert on them), and
the compare counts the centre-median rows as FAILS only when the two statements
are equal; when they differ the rows print as ADVISORY, not counted. Re-seeding
on acceptance records the new statement and re-arms the check. No threshold is
added: the rule is the equality of two recorded strings. corner_spread_pct and
edge_dipole_x are always hard — they are the structure measures.

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
    """The rule, PURE: (fails, advisories) of the measured `now` against the
    baseline's measures `b` under `tol`. The four checks are the ones this guard
    always ran; the only routing is the centre-median loop, which appends to
    `advisories` instead of `fails` when the two normalization statements
    differ (docstring: THE LEVEL MEASURE IS ADVISORY ...)."""
    spread, dip = now["corner_spread_pct"], now["edge_dipole_x"]
    chans = now["centre_median_per_channel"]
    fails, advisories = [], []
    level = (fails if now.get("stacknrm", DEFAULT_NRM) == b.get("stacknrm", DEFAULT_NRM)
             else advisories)

    if spread > tol["corner_spread_pct_max_abs"]:
        fails.append(f"corner_spread_pct {spread} exceeds absolute ceiling "
                     f"{tol['corner_spread_pct_max_abs']}")
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
    return fails, advisories


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
    cases = [  # (label, now, baseline, expected fails, advisory expected)
        ("same STACKNRM, centre +30% -> RED",            now(1.30), base, 1 * 3, False),
        ("STACKNRM differs, centre +80% -> ADVISORY",   now(1.80, nrm="addscale"), base, 0, True),
        ("STACKNRM differs, corner_spread +2.0 -> RED", now(1.80, spread=2.7, nrm="addscale"), base, 1, True),
        ("same STACKNRM, centre +10% -> PASS",           now(1.10), base, 0, False),
        ("STACKNRM differs, edge_dipole +0.10 -> RED",  now(1.80, dip=0.104, nrm="addscale"), base, 1, True),
        ("baseline without the field, default product +30% -> RED", now(1.30), old_base, 3, False),
        ("baseline without the field, addscale product +80% -> ADVISORY", now(1.80, nrm="addscale"), old_base, 0, True),
    ]
    bad = 0
    for label, n, bl, nf, adv in cases:
        fails, advisories = compare(n, bl, DEFAULT_TOL)
        ok = (len(fails) == nf) and (bool(advisories) == adv)
        print(f"  selftest {'ok  ' if ok else 'WRONG'} [{len(fails)} fail, "
              f"{len(advisories)} advisory] {label}")
        bad |= not ok
    if bad:
        print("baseline_guard --selftest: FAIL — the rule does not fire as stated")
        return 1
    print("OK: baseline_guard compare rule — 7 cases: RED on level under a matching "
          "STACKNRM, ADVISORY under a differing one, RED on structure either way, "
          "PASS on ordinary variation, field-less baselines read as the default")
    return 0


def _measure(stack, workdir, tag, box, margin):
    """Siril `stat` on five regions via regional_stat.py. Returns per-channel
    medians. The .ssf and Siril workdir land beside the record, which must be
    under $HOME — the Siril flatpak has a private /tmp."""
    out = os.path.join(workdir, f"baseline_{tag}.json")
    r = subprocess.run([sys.executable, REGIONAL, stack, out,
                        f"--box={box}", f"--margin={margin}"],
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


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("set")
    ap.add_argument("stack")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--reseed", action="store_true")
    ap.add_argument("--note", default="")
    a = ap.parse_args()

    sess = os.path.basename(os.path.normpath(a.session))
    dsdir = os.path.join(REPO, "datasets", sess, a.set)
    work = os.path.join(dsdir, "qa_work")
    os.makedirs(work, exist_ok=True)
    bpath = os.path.join(dsdir, "baseline.json")
    stack = os.path.abspath(a.stack)
    if not os.path.exists(stack):
        sys.exit(f"baseline_guard: no such stack: {stack}")

    corners, craw = _measure(stack, work, "corners", 400, 200)
    edge, _ = _measure(stack, work, "edge", 80, 2)
    spread, dip = _derive(corners, edge)
    chans = {k: v["median"] for k, v in craw["center"].items()}
    # the product's own normalization statement, header-only; absent = the
    # pre-change default (see DEFAULT_NRM)
    nrm = str(fits.getheader(stack).get("STACKNRM", DEFAULT_NRM))
    now = {"corner_spread_pct": spread, "edge_dipole_x": dip,
           "centre_median_per_channel": chans, "stacknrm": nrm,
           "stack": os.path.relpath(stack, REPO), "stack_id": _sha(stack)}

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
        json.dump(rec, open(bpath, "w"), indent=1)
        print(f"seeded {bpath}")
        print(f"  corner_spread_pct {spread}   edge_dipole_x {dip:+.4f}")
        return 0

    if not os.path.exists(bpath):
        sys.exit(f"baseline_guard: no baseline at {bpath} — seed one with --seed "
                 "once a human has accepted this product.")
    base = json.load(open(bpath))
    b, tol = base["measures"], base.get("tolerances", DEFAULT_TOL)
    fails, advisories = compare(now, b, tol)

    print(f"baseline_guard {sess}/{a.set}")
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
    if fails:
        print("\nREGRESSION — this product no longer measures like the accepted one:")
        for f in fails:
            print(f"  - {f}")
        print("\nIf the change is DELIBERATE and a human has judged it better, re-seed:")
        print(f"  {sys.argv[0]} {a.session} {a.set} {a.stack} --reseed --note='...'")
        return 1
    print("\nPASS" + (" (with advisory)" if advisories else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
