#!/usr/bin/env python3
"""One-command no-regression sweep over every registered dataset.

Usage:
  sweep.py                          # sweep everything with a baseline.json
  sweep.py --only 07-02-26/set-03 [--only ...]
  sweep.py --rebaseline imx585c/m74_toa130 [--rebaseline ...]
  sweep.py --determinism            # render each target TWICE, compare bytes
  sweep.py --keep                   # keep the sweep render artifacts

The acceptance contract (README "How a change is accepted") in one
command. For each datasets/<session>/<set>/baseline.json whose pinned
stack exists on this machine:

  1. render with starcomb (knobs from the dataset recipe),
  2. GATE: the starless render must PASS bg_qa — thresholds never loosen,
  3. star shells: aura_lum must sit inside its WARN bound,
  4. declared-delta detector: every metric is diffed against the recorded
     baseline; drift is REPORTED (a delta is expected under a declared
     change, a silent one is the bug),
  5. reproducibility: when the stack still matches its recorded sha256,
     the artifact hashes are compared — IDENTICAL means the render
     byte-reproduces the baseline; DELTA means code changed the output
     (declare it, judge it if aesthetic, then --rebaseline + tag).

--determinism renders twice and compares the two FRESH runs byte-for-byte
(the contract's check 1, independent of any baseline). --rebaseline
re-measures and REWRITES baseline.json from the rendered output (never
edit one by hand); the approved/date provenance fields are preserved.

A dataset whose stack is absent (third-party data not on this machine)
is SKIPPED loudly, never silently passed. Exit 0 = no regressions.

Renders land in <session>/results/ tagged `sweep` and are deleted after
hashing unless --keep; the summary prints to stdout (pipe it into a log
if a record is wanted — baselines themselves are the durable record).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
AURA_BOUND = am.STAR_SHELL_WARN["aura_lum"]
# gate + shell numbers the sweep records and diffs, pulled from starcomb's
# metrics dict: (json section, key)
TRACKED = [("qa_starless", "color"), ("qa_starless", "grad"),
           ("qa_starless", "resid"), ("qa_starless", "ring_l"),
           ("qa_starless", "floor"), ("star_shells", "aura_lum"),
           ("star_shells", "shell_chroma")]


def sha256(path, bufsize=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def targets(args):
    """(session, set, dsdir) triples to sweep: --only/--rebaseline
    selections, else every dataset dir carrying a baseline.json (for
    --rebaseline, the dir needs only a recipe or geometry to exist)."""
    picks = args.rebaseline or args.only
    if picks:
        out = []
        for p in picks:
            session, set_name = p.split("/", 1)
            out.append((session, set_name,
                        os.path.join(REPO, "datasets", session, set_name)))
        return out
    root = os.path.join(REPO, "datasets")
    out = []
    for session in sorted(os.listdir(root)):
        sd = os.path.join(root, session)
        if not os.path.isdir(sd):
            continue
        for set_name in sorted(os.listdir(sd)):
            dsdir = os.path.join(sd, set_name)
            if os.path.exists(os.path.join(dsdir, "baseline.json")):
                out.append((session, set_name, dsdir))
    return out


def render_once(session, set_name, stack_rel, keep, run_tag):
    """One starcomb render; returns (metrics dict incl. artifact paths +
    hashes). Artifacts are hashed, then deleted unless keep."""
    sdir = os.path.join(REPO, session)
    stack = os.path.join(sdir, stack_rel)
    mjson = os.path.join(sdir, "work", f"sweep_{set_name}_{run_tag}.json")
    cmd = [sys.executable,
           os.path.join(REPO, "scripts", "render", "starcomb.py"),
           session, set_name, "--stack", stack, "--lossless",
           "--tag", run_tag, "--metrics-out", mjson]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    if r.returncode != 0 or not os.path.exists(mjson):
        return {"error": (r.stdout[-1500:] + "\n" + r.stderr[-500:]).strip()}
    met = json.load(open(mjson))
    os.remove(mjson)
    jpg = met.pop("jpg")
    arts = {"jpg": jpg, "png": jpg[:-4] + ".png",
            "png16": jpg[:-4] + "_16bit.png",
            "starless_jpg": jpg[:-4] + "_starless.jpg"}
    met["artifact_sha256"] = {k: sha256(p) for k, p in arts.items()
                              if os.path.exists(p)}
    if not keep:
        for p in arts.values():
            if os.path.exists(p):
                os.remove(p)
    else:
        met["artifact_paths"] = arts
    return met


def flat(met):
    return {f"{sec}.{key}": met.get(sec, {}).get(key)
            for sec, key in TRACKED}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", default=[],
                    help="restrict to <session>/<set> (repeatable)")
    ap.add_argument("--rebaseline", action="append", default=[],
                    help="re-measure and REWRITE baseline.json for "
                         "<session>/<set> (repeatable)")
    ap.add_argument("--determinism", action="store_true",
                    help="render each target twice and require the two "
                         "fresh runs to be byte-identical")
    ap.add_argument("--keep", action="store_true",
                    help="keep the sweep render artifacts")
    args = ap.parse_args()

    stamp = time.strftime("%Y%m%d_%H%M%S")
    rows, failed = [], []
    for session, set_name, dsdir in targets(args):
        name = f"{session}/{set_name}"
        bl_path = os.path.join(dsdir, "baseline.json")
        bl = json.load(open(bl_path)) if os.path.exists(bl_path) else {}
        rebase = name in (args.rebaseline or [])
        if not bl and not rebase:
            continue
        stack_rel = bl.get("stack")
        if not stack_rel:
            # first baseline for this dataset: resolve the render input by
            # the pipeline's naming convention — the SPCC-calibrated stack
            # when one exists (colour sets), else the plain stack (mono
            # sets skip SPCC)
            for cand in (f"results/stack_{set_name}_norgbeq_spcc.fit",
                         f"results/stack_{set_name}_spcc.fit",
                         f"results/stack_{set_name}.fit"):
                if os.path.exists(os.path.join(REPO, session, cand)):
                    stack_rel = cand
                    break
            stack_rel = stack_rel or f"results/stack_{set_name}.fit"
            print(f"== {name}: first baseline — input resolved to "
                  f"{stack_rel}")
            if "_spcc" not in stack_rel:
                # a 3-channel stack without an _spcc product is a colour
                # set about to be baselined UN-colour-calibrated — legal
                # for mono (SPCC has nothing to calibrate) but a mistake
                # everywhere else, so say it before it is pinned
                p = os.path.join(REPO, session, stack_rel)
                if os.path.exists(p):
                    import re as _re
                    raw = open(p, "rb").read(2880 * 4).decode(
                        "ascii", "replace")
                    m3 = _re.search(r"NAXIS3\s*=\s*(\d+)", raw)
                    if m3 and int(m3.group(1)) >= 3:
                        print(f"== {name}: NOTICE — no _spcc stack found; "
                              "this pins a 3-channel stack BEFORE colour "
                              "calibration (solve + spcc_run first unless "
                              "that is deliberate)")
        stack = os.path.join(REPO, session, stack_rel)
        if not os.path.exists(stack):
            print(f"== {name}: SKIP — stack {stack_rel} absent on this "
                  "machine (third-party data not downloaded?)")
            rows.append((name, "SKIP", "stack absent"))
            continue
        print(f"== {name}: rendering ({stack_rel})", flush=True)
        stack_sha = sha256(stack)
        met = render_once(session, set_name, stack_rel, args.keep,
                          f"sweep{stamp}")
        if "error" in met:
            print(f"   RENDER FAILED:\n{met['error']}")
            rows.append((name, "FAIL", "render error"))
            failed.append(name)
            continue

        notes = []
        gate_ok = bool(met["qa_starless"]["pass"])
        aura = met["star_shells"]["aura_lum"]
        aura_ok = aura is None or aura <= AURA_BOUND
        if not gate_ok:
            notes.append("GATE FAIL")
        if not aura_ok:
            notes.append(f"aura {aura:+.1f} > {AURA_BOUND}")

        if args.determinism:
            met2 = render_once(session, set_name, stack_rel, False,
                               f"sweep{stamp}b")
            if "error" in met2:
                notes.append("2nd render FAILED")
            elif met2["artifact_sha256"] != met["artifact_sha256"]:
                notes.append("NONDETERMINISTIC (two fresh runs differ)")
            else:
                notes.append("deterministic")

        if bl:
            same_stack = bl.get("stack_sha256") == stack_sha
            if same_stack and bl.get("artifact_sha256"):
                if bl["artifact_sha256"] == met["artifact_sha256"]:
                    notes.append("= baseline bytes")
                else:
                    notes.append("DELTA vs baseline (declare/judge/"
                                 "--rebaseline)")
            elif not same_stack:
                notes.append("stack rebuilt since baseline (gate-only "
                             "check)")
            drift = []
            for k, v in flat(met).items():
                b = bl.get("metrics", {}).get(k)
                if b is not None and v is not None and abs(v - b) > 0.05:
                    drift.append(f"{k} {b:g}->{v:g}")
            if drift:
                notes.append("drift: " + ", ".join(drift))

        if rebase:
            new_bl = {
                "_readme": "Measured no-regression record — written by "
                           "sweep.py --rebaseline, never by hand.",
                "dataset": name,
                "approved": bl.get("approved"),
                "stack": stack_rel,
                "stack_sha256": stack_sha,
                "rebuild": f"python3 scripts/render/starcomb.py {session} "
                           f"{set_name} --stack {session}/{stack_rel} "
                           "--lossless",
                "metrics": flat(met),
                "gate_pass": gate_ok,
                "artifact_sha256": met["artifact_sha256"],
                "recipe": met.get("recipe"),
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "git": subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                    capture_output=True, text=True).stdout.strip() or None,
            }
            with open(bl_path, "w") as f:
                json.dump(new_bl, f, indent=1)
            notes.append("REBASELINED")

        ok = gate_ok and aura_ok and \
            not any(n.startswith("NONDETERMINISTIC") or n == "2nd render FAILED"
                    for n in notes)
        verdict = "PASS" if ok else "FAIL"
        if not ok:
            failed.append(name)
        qs = met["qa_starless"]
        print(f"   {verdict}  gate color {qs['color']:.1f} grad "
              f"{qs['grad']:.1f} blotch {qs['resid']:.1f} rings "
              f"{qs['ring_l']:.1f} | aura "
              f"{aura if aura is None else format(aura, '+.1f')} | "
              + "; ".join(notes))
        rows.append((name, verdict, "; ".join(notes)))

    print("\n== sweep summary ==")
    w = max((len(r[0]) for r in rows), default=10)
    for name, verdict, note in rows:
        print(f"  {name.ljust(w)}  {verdict:5s}  {note}")
    if failed:
        print(f"\nREGRESSIONS: {', '.join(failed)}")
        sys.exit(1)
    print("\nno regressions")


if __name__ == "__main__":
    main()
