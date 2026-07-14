#!/usr/bin/env python3
"""One-command no-regression sweep over every registered dataset.

Usage:
  sweep.py                          # sweep everything with a baseline.json
  sweep.py --only <session>/<set> [--only ...]
  sweep.py --rebaseline <session>/<set> [--rebaseline ...]
  sweep.py --rebaseline <session>/<set> --ack-color-scope
  sweep.py --determinism            # render each target TWICE, compare bytes
  sweep.py --keep                   # keep the sweep render artifacts

The acceptance contract (README "How a change is accepted") in one
command. For each datasets/<session>/<set>/baseline.json whose pinned
stack exists on this machine:

  1. render with starcomb (knobs from the dataset recipe),
  2. GATE: the starless render must PASS bg_qa — thresholds never loosen.
     One explicit, per-dataset exception keeps emission-flooded fields
     inside the regression net instead of outside every check: a baseline
     recorded with --ack-color-scope (legal ONLY when color is the sole
     failing metric — real sky colour the current color scope cannot
     admit) enforces the achromatic thresholds unchanged and grades color
     ONE-SIDED against the recorded value (worsening fails). Full ≤limit
     color admission still waits on the color-gate redesign; the ack is
     tracking, never judgment,
  3. star shells: aura_lum must NOT WORSEN vs the recorded baseline
     (regression semantics — a clean dataset rotting from +2.0 toward the
     defect class fails long before any absolute line). The absolute
     audit WARN bound applies only when no baseline number exists, and
     recording a baseline above that bound requires --ack-aura-warn, so
     the tolerance cannot ratchet a dataset over the bound unnoticed,
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
import shutil
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
import bg_qa  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
AURA_BOUND = am.STAR_SHELL_WARN["aura_lum"]
# Aura no-regression tolerance vs the recorded baseline. The metric's
# calibrated separation is a clean recipe +2.0 vs a defective render +12.0, and its
# rendering-context sensitivity is ±0.5 (measured: a 128 px frame trim
# alone moves it +0.5 through the top-500 anchor population, no shell
# physics involved) — so 0.5 sits above context wiggle and far below the
# smallest real step toward the defect class. A slow ratchet across
# rebaselines is capped by the --ack-aura-warn refusal at the audit bound.
AURA_WORSEN_TOL = 0.5
# One-sided color tolerance for scope-ACKED baselines. The render is
# byte-deterministic from its stack, so on an unchanged stack the color
# metric reproduces exactly; 0.5 covers stack-rebuild jitter while any
# real added cast (the calibrated defect class is ~8 counts) fails by an
# order of magnitude. Deliberately recording a higher color is possible
# only through --rebaseline with the ack flag passed again — the same
# explicit-act anti-ratchet as --ack-aura-warn.
COLOR_WORSEN_TOL = 0.5
# gate + shell numbers the sweep records and diffs, pulled from starcomb's
# metrics dict: (json section, key)
TRACKED = [("qa_starless", "color"), ("qa_starless", "grad"),
           ("qa_starless", "resid"), ("qa_starless", "ring_l"),
           ("qa_starless", "floor"), ("star_shells", "aura_lum"),
           ("star_shells", "shell_chroma")]


def aura_verdict(aura, bl_aura):
    """Shell-audit regression check: (ok, note). Baseline-relative — FAIL
    only when the render's aura WORSENS beyond AURA_WORSEN_TOL vs the
    recorded baseline (an improvement or small context wiggle passes; a
    clean +2.0 dataset rotting to +3.5 fails even though it is under the
    absolute audit bound). Without a baseline number the absolute audit
    WARN bound is the only available reference."""
    if aura is None:
        return True, None
    if bl_aura is None:
        if aura <= AURA_BOUND:
            return True, None
        return False, (f"aura {aura:+.1f} > {AURA_BOUND} "
                       "(audit bound; no baseline aura)")
    if aura <= bl_aura + AURA_WORSEN_TOL:
        return True, None
    return False, (f"aura worsened {bl_aura:+.1f} -> {aura:+.1f} "
                   f"(tol {AURA_WORSEN_TOL})")


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
            "starless_jpg": jpg[:-4] + "_starless.jpg",
            "starless_png": jpg[:-4] + "_starless.png",
            "starless_png16": jpg[:-4] + "_starless_16bit.png"}
    met["artifact_sha256"] = {k: sha256(p) for k, p in arts.items()
                              if os.path.exists(p)}
    if not keep:
        for p in arts.values():
            if os.path.exists(p):
                os.remove(p)
        # the diagnostic side files starcomb wrote this build (a metrics
        # sidecar + the per-stage sequence): clean with the artifacts so a
        # sweep leaves no orphans (they are NOT hashed — not the artifact)
        sc = jpg[:-4] + ".metrics.json"
        if os.path.exists(sc):
            os.remove(sc)
        sd = jpg[:-4] + "_stages"
        if os.path.isdir(sd):
            shutil.rmtree(sd, ignore_errors=True)
    else:
        met["artifact_paths"] = arts
    return met


def flat(met):
    return {f"{sec}.{key}": met.get(sec, {}).get(key)
            for sec, key in TRACKED}


def recipe_approved(dsdir):
    """Approval provenance for a FIRST baseline of an approved look: the
    recipe.json carries the approval record (status + approved block), and
    a baseline must never read approved:null while its recipe says
    approved — one truth, copied at record time (later rebaselines
    preserve the baseline's own field)."""
    try:
        r = json.load(open(os.path.join(dsdir, "recipe.json")))
    except (OSError, ValueError):
        return None
    if r.get("status") == "approved":
        return r.get("approved") or {"status": "approved"}
    return None


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
    ap.add_argument("--ack-aura-warn", action="store_true",
                    help="allow --rebaseline to record an aura_lum above "
                         "the audit WARN bound — a deliberate, "
                         "acknowledged decision, never a default")
    ap.add_argument("--ack-color-scope", action="store_true",
                    help="allow --rebaseline to record a baseline whose "
                         "ONLY failing gate metric is color (an emission-"
                         "flooded sky the current color scope cannot "
                         "admit): achromatic thresholds stay enforced and "
                         "color is graded one-sided vs the record — "
                         "explicit per-dataset tracking, never a gate "
                         "loosening")
    args = ap.parse_args()

    stamp = time.strftime("%Y%m%d_%H%M%S")
    rows, failed = [], []

    # standing hand-roll rule guard (CLAUDE.md orchestrate-not-hand-roll):
    # keeps the render chain's processing operators catalogued + honest and
    # fails the sweep on a NEW unregistered hand-rolled processing function
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import hand_roll_audit
    if not hand_roll_audit.audit()[0]:
        failed.append("hand-roll-audit")
        rows.append(("hand-roll-audit", "FAIL", "unregistered/incoherent "
                     "processing operator — see scripts/render/operators.json"))

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
            # when one exists (colour sets; composed targets carry _comp),
            # else the plain stack (mono sets skip SPCC)
            for cand in (f"results/stack_{set_name}_norgbeq_spcc.fit",
                         f"results/stack_{set_name}_comp_spcc.fit",
                         f"results/stack_{set_name}_spcc.fit",
                         f"results/stack_{set_name}_comp.fit",
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
        qs = met["qa_starless"]
        gate_ok = bool(qs["pass"])
        achrom_ok = bool(qs["ok_grad"] and qs["ok_resid"] and qs["ok_rings"])
        color = float(qs["color"])
        # a color-scope ACK is active from the recorded baseline, or on the
        # rebaseline run that is recording it (the flag is the explicit act)
        ack_active = bool(bl.get("color_scope_ack")) or \
            (rebase and args.ack_color_scope)
        aura = met["star_shells"]["aura_lum"]
        bl_aura = bl.get("metrics", {}).get("star_shells.aura_lum") \
            if bl else None
        aura_ok, aura_note = aura_verdict(aura, bl_aura)
        gate_req_ok = gate_ok
        if not gate_ok:
            if ack_active and achrom_ok and not qs["ok_color"]:
                # scope-ACKED: achromatic thresholds enforced unchanged;
                # color graded one-sided against the record
                bl_color = bl.get("metrics", {}).get("qa_starless.color") \
                    if bl else None
                if bl_color is not None and \
                        color > bl_color + COLOR_WORSEN_TOL:
                    notes.append(f"color worsened {bl_color:g} -> {color:g}"
                                 f" (tol {COLOR_WORSEN_TOL}) vs the "
                                 "scope-ack record")
                else:
                    gate_req_ok = True
                    notes.append(f"color {color:.1f} scope-ACK (sole "
                                 "failing metric; achromatics + one-sided "
                                 "color enforced — full admission waits on "
                                 "the color-gate redesign)")
            else:
                notes.append("GATE FAIL")
        elif bl.get("color_scope_ack"):
            notes.append("color now within the gate — rebaseline to drop "
                         "the scope ack")
        if aura_note:
            notes.append(aura_note)

        if args.determinism:
            # COLD for real: the render caches are keyed by the stack's
            # size+mtime, so without clearing them the second render
            # reuses the first's GraXpert/separation outputs and the
            # check never exercises the heavy stages (measured: that
            # blind spot hid a real render drift on one dataset until an
            # unrelated cache prune exposed it)
            st = os.stat(stack)
            key = f"{st.st_size}_{int(st.st_mtime)}"
            wdir = os.path.join(REPO, session, "work")
            import glob as _glob
            cleared = 0
            for pat in (f"bgelin_{key}*.fit", f"gx_{key}.fits",
                        os.path.join("starsep", f"*_{key}*")):
                for p in _glob.glob(os.path.join(wdir, pat)):
                    os.remove(p)
                    cleared += 1
            met2 = render_once(session, set_name, stack_rel, False,
                               f"sweep{stamp}b")
            if "error" in met2:
                notes.append("2nd render FAILED")
            elif met2["artifact_sha256"] != met["artifact_sha256"]:
                notes.append("NONDETERMINISTIC (two cold runs differ, "
                             f"{cleared} caches cleared)")
            else:
                notes.append(f"deterministic (cold: {cleared} caches "
                             "cleared before rerun)")

        if bl:
            same_stack = bl.get("stack_sha256") == stack_sha
            if same_stack and bl.get("artifact_sha256"):
                # byte-compare over the BASELINE's recorded artifacts: a
                # recorded artifact that changed or vanished is the
                # regression; an artifact class ADDED since the baseline
                # is a declared addition, reported until a rebaseline
                # records it
                bl_arts = bl["artifact_sha256"]
                got = met["artifact_sha256"]
                if all(got.get(k) == v for k, v in bl_arts.items()):
                    notes.append("= baseline bytes")
                    extra = sorted(set(got) - set(bl_arts))
                    if extra:
                        notes.append(f"new artifacts {extra} "
                                     "(--rebaseline to record)")
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

        refused = False
        if rebase and aura is not None and aura > AURA_BOUND \
                and not args.ack_aura_warn:
            # recording a baseline above the audit WARN bound must be a
            # deliberate act, or the worsening tolerance could ratchet a
            # dataset over the bound one rebaseline at a time
            notes.append(f"REBASELINE REFUSED: aura {aura:+.1f} over the "
                         f"audit WARN {AURA_BOUND} — pass --ack-aura-warn "
                         "to record it deliberately")
            rebase = False
            refused = True
        if rebase and not gate_ok:
            # a baseline is the record of a passing state; the only gate
            # failure a record may carry is the acknowledged color scope
            # (real emission-flooded sky, color the SOLE failing metric)
            if not (achrom_ok and not qs["ok_color"]):
                notes.append("REBASELINE REFUSED: gate fails on an "
                             "achromatic metric — a chain defect, never "
                             "sky-colour scope")
                rebase = False
                refused = True
            elif not args.ack_color_scope:
                notes.append(f"REBASELINE REFUSED: color {color:.1f} over "
                             f"the gate limit {bg_qa.COLOR_DEV_MAX:g} — "
                             "pass --ack-color-scope to record a "
                             "scope-acknowledged baseline (achromatics "
                             "stay enforced; color graded one-sided)")
                rebase = False
                refused = True
        if rebase and args.ack_color_scope and gate_ok:
            notes.append("color within the gate — no scope ack recorded")
        if rebase:
            new_bl = {
                "_readme": "Measured no-regression record — written by "
                           "sweep.py --rebaseline, never by hand.",
                "dataset": name,
                "approved": bl.get("approved") or recipe_approved(dsdir),
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
            if not gate_ok and args.ack_color_scope:
                # reaching here with a failing gate means the refusals
                # above admitted it: color is the sole failing metric and
                # the ack was passed — record the acknowledgment
                new_bl["color_scope_ack"] = True
            with open(bl_path, "w") as f:
                json.dump(new_bl, f, indent=1)
            notes.append("REBASELINED")

        ok = gate_req_ok and aura_ok and not refused and \
            not any(n.startswith("NONDETERMINISTIC") or n == "2nd render FAILED"
                    for n in notes)
        verdict = "PASS" if ok else "FAIL"
        if not ok:
            failed.append(name)
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
