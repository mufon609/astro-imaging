#!/usr/bin/env python3
"""Common-reference partitioned integration for raw sets whose single-pass
intermediates exceed free disk.

A 24.5 MP camera-raw set needs ~294 MB of simultaneous 16-bit intermediates
per frame on the monolithic path (debayered calibrated + registered
copies), so a 240-frame set wants ~70 GB where this rig has ~5 GB free.
This runner keeps the standard path's SEMANTICS but bounds the footprint:
the set stacks in time-contiguous partitions that all register 1-pass to
ONE pinned reference frame (a copy of that frame is staged into every
partition and excluded from its stack), so every partition stack is
pixel-aligned by construction — one interpolation total, one normalization
target — and the final product is the frame-count-weighted mean of the
partition stacks, accumulated incrementally so only one partition stack
ever exists on disk.

Routes (--route, explicit; the operator/recipe decides on measurement):
  flat      calibrate with master dark + master flat (matched-flat
            template semantics). Flats calibrate with a real bias master
            when biases/ holds frames, else with siril's documented
            synthetic bias for CMOS (-bias="=N", N = measured master-dark
            median ADU).
  selfflat  the repo's self-flat branch (median -> V(r) isotonic gray
            gain -> rechroma -> V2 divide), fitted ONCE from a clear-frame
            subset (--gain-subset) and applied per partition. Faithful to
            the branch templates: rechroma shifts channels to the V1
            levels; division uses the V2 gain fitted from the shifted
            frames' own median. Use when no flat matches OR a flat is
            measured-unusable (this session: flat corner/center 0.19 vs
            the lights' own sky falloff 0.5-0.7 — flat-source falloff,
            division would over-brighten corners ~3x).

Divergences from the monolithic templates, each carried deliberately:
  - reference PINNED (setref + 1-pass register), not 2-pass auto-picked:
    the common-reference construction requires it, and a pinned clean
    reference guards against reference capture by a defect-class frame
    population (measured: cloud-band frames elect their own frame and
    cross-match on cloud texture on CFA data — NOTES dead ends).
  - registration + frame QA on DEBAYERED calibrated frames (measured:
    the CFA lattice false-matches cloud texture — NOTES dead ends).
  - per-partition rejection (rej 3 3 over the partition) instead of
    full-set rejection; partition means combine by weighted mean.
    Transients are per-frame events, so partition-local rejection sees
    them at the same per-pixel minority ratio as a full-set stack.
  - the final combine is a numpy weighted mean in float64, written as
    float32 in the [0,1] ushort convention (the same scale siril's
    -output_norm keeps); partition stacks skip -output_norm so all
    partitions share the common reference's addscale scale.

Frame identity: "n" = 1-based position in the SORTED raw file list of the
set (== siril convert order of the full set == the registration
inspection's n). --exclude names these n; exclusion is applied at staging
(excluded frames never convert), implementing the recipe "stack" block's
exclude policy — provenance printed per run.

Usage:
  partitioned_stack.py <session> <set> --ref N --route {flat,selfflat}
      [--part-size 14] [--exclude n,n,...] [--gain-subset n,n,...]
      [--variant e0] [--resume] [--masters-only]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np

# scripts/lib holds the shared libs (astrometrics, bg_qa); locate it by
# walking up from this file so one bootstrap works at any nesting depth.
_libdir = os.path.dirname(os.path.abspath(__file__))
while _libdir != os.path.dirname(_libdir):
    if os.path.isdir(os.path.join(_libdir, "lib")):
        sys.path.insert(0, os.path.join(_libdir, "lib"))
        break
    _libdir = os.path.dirname(_libdir)
import astrometrics as am  # noqa: E402

# _libdir is the scripts/ dir (it holds lib/); the repo root is its parent
_repo = os.path.dirname(_libdir)
sys.path.insert(0, os.path.join(_libdir, "qa"))
from inspect_stage import parse_seq_regdata  # noqa: E402

RAW_EXTS = (".dng", ".nef", ".cr2", ".cr3", ".arw", ".raf", ".orf",
            ".rw2", ".pef", ".srw")


def raw_list(d):
    return sorted(f for f in os.listdir(d)
                  if f.lower().endswith(RAW_EXTS))


def siril_run(session_dir, script_path, log_path):
    cmd = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril",
           "-d", session_dir, "-s", script_path]
    with open(log_path, "w") as lf:
        p = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT)
    return p.returncode


def script_failed(log_path, out_file=None):
    """A siril script run is judged by its own success marker plus the
    expected artifact — NOT by scanning for error-shaped lines: siril
    prints a benign 'Reading sequence failed, file cannot be opened'
    probe before every convert. Returns None on success, else a short
    diagnostic list."""
    ok = False
    context = []
    bad = re.compile(r"(command .* failed|Unknown command|Error in command"
                     r"|Script execution failed)", re.IGNORECASE)
    with open(log_path) as f:
        for line in f:
            if "Script execution finished successfully" in line:
                ok = True
            if bad.search(line):
                context.append(line.strip())
    if ok and (out_file is None or os.path.isfile(out_file)):
        return None
    if out_file and not os.path.isfile(out_file):
        context.append(f"missing expected output {out_file}")
    return context or ["no success marker in log"]


def run_script(S, W, name, lines, expect=None):
    gen = os.path.join(W, f"{name}.gen.ssf")
    log = os.path.join(W, f"{name}.log")
    with open(gen, "w") as f:
        f.write("\n".join(lines) + "\n")
    rc = siril_run(S, gen, log)
    errs = script_failed(log, expect)
    if rc != 0 or errs:
        sys.exit(f"{name} failed (rc={rc}); log {log}: {(errs or [])[:4]}")
    return log


def reg_total(log_path):
    """Last 'Total: N failed, M registered' from a siril log; None when
    absent (callers treat that as a parse failure, never as 0)."""
    tot = None
    with open(log_path) as f:
        for line in f:
            m = re.search(r"Total: (\d+) failed, (\d+) registered", line)
            if m:
                tot = (int(m.group(1)), int(m.group(2)))
    return tot


def stat_median(log_path):
    """Median from a `stat` print (G layer on RGB, B&W on mono), in the
    loaded integer scale."""
    med = None
    with open(log_path) as f:
        for line in f:
            m = re.search(r"(Green|B&W) layer:.*Median: ([0-9.]+)", line)
            if m:
                med = float(m.group(2))
    return med


def measure_median_adu(fits_path):
    d, _ = am.read_fits(fits_path)
    return int(round(float(np.median(d)) * 65535.0))


def rm_glob(d, prefix, keep_seq=True):
    for p in os.listdir(d):
        if p.startswith(prefix) and not (keep_seq and p.endswith(".seq")):
            os.remove(os.path.join(d, p))


def build_master_dark(S, W):
    md = os.path.join(W, "masters", "dark_master.fit")
    os.makedirs(os.path.join(W, "masters"), exist_ok=True)
    if not os.path.isfile(md):
        darks = raw_list(os.path.join(S, "darks"))
        print(f"=== master dark ({len(darks)} frames) ===", flush=True)
        # rice-compressed conversion transients (halves the peak on this
        # disk); the master itself is written uncompressed so every
        # existing consumer reads it unchanged
        run_script(S, W, "pmaster_dark", [
            "requires 1.4.0", "set16bits", "setcompress 1 -type=rice 16",
            "cd darks", "convert dk -out=../work", "cd ../work",
            "setcompress 0",
            "stack dk rej 3 3 -nonorm -out=masters/dark_master", "close",
        ], md)
        rm_glob(W, "dk_", keep_seq=False)
    dark_med = measure_median_adu(md)
    print(f"master dark median: {dark_med} ADU", flush=True)
    return dark_med


def build_master_flat(S, W, dark_med):
    mf = os.path.join(W, "masters", "flat_master.fit")
    if os.path.isfile(mf):
        return mf
    flats_dir = os.path.join(S, "flats")
    flats = raw_list(flats_dir) if os.path.isdir(flats_dir) else []
    if not flats:
        sys.exit("--route flat but no frames in flats/")
    biases_dir = os.path.join(S, "biases")
    biases = raw_list(biases_dir) if os.path.isdir(biases_dir) else []
    if biases:
        biasopt = "-bias=masters/bias_master"
        print(f"=== master bias ({len(biases)} frames) ===", flush=True)
        run_script(S, W, "pmaster_bias", [
            "requires 1.4.0", "set16bits", "setcompress 1 -type=rice 16",
            "cd biases", "convert bias -out=../work", "cd ../work",
            "setcompress 0",
            "stack bias rej 3 3 -nonorm -out=masters/bias_master", "close",
        ], os.path.join(W, "masters", "bias_master.fit"))
        rm_glob(W, "bias_", keep_seq=False)
    else:
        biasopt = f'-bias="={dark_med}"'
        print(f"biases/ empty or absent: flats calibrate with SYNTHETIC "
              f"bias {biasopt} (siril's documented CMOS offset handling; "
              f"value = measured master-dark median)", flush=True)
    print(f"=== master flat ({len(flats)} frames) ===", flush=True)
    run_script(S, W, "pmaster_flat", [
        "requires 1.4.0", "set16bits", "setcompress 1 -type=rice 16",
        "cd flats", "convert fl -out=../work", "cd ../work",
        f"calibrate fl {biasopt}", "setcompress 0",
        "stack pp_fl rej 3 3 -norm=mul -out=masters/flat_master", "close",
    ], mf)
    with open(os.path.join(W, "masters", "flat_bias_provenance.txt"),
              "w") as f:
        f.write(f"{biasopt}\n")
    rm_glob(W, "fl_", keep_seq=False)
    rm_glob(W, "pp_fl_", keep_seq=False)
    return mf


def build_selfflat_gain(S, W, set_name, names, subset):
    """The self-flat branch's gain estimation, run ONCE on a clear-frame
    subset (V is the optics' property; the median needs clean sky, not
    every frame): calibrate -> 32-bit median (norm=mul) -> V1 fit (levels)
    -> seqsubsky 1 -> rechroma to the V1 levels -> 32-bit median (nonorm)
    -> V2 fit. Ships masters/selfflat_gain.fit (V2, the divisor) and
    masters/selfflat_levels.json (the V1 levels rechroma used — partitions
    must shift with the SAME levels the V2 median was built from)."""
    gain = os.path.join(W, "masters", "selfflat_gain.fit")
    levels = os.path.join(W, "masters", "selfflat_levels.json")
    if os.path.isfile(gain) and os.path.isfile(levels):
        print("self-flat gain already built, reusing", flush=True)
        return
    print(f"=== self-flat gain from {len(subset)} subset frames "
          f"(n={subset[0]}..{subset[-1]}) ===", flush=True)
    sfstage = os.path.join(W, "sfstage")
    sfwork = os.path.join(W, "sfwork")
    for d in (sfstage, sfwork):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    for n in subset:
        os.symlink(os.path.join(S, set_name, names[n - 1]),
                   os.path.join(sfstage, names[n - 1]))
    run_script(S, W, "sf_g1a", [
        "requires 1.4.0", "set16bits", "setcompress 1 -type=rice 16",
        "cd work/sfstage", "convert light -out=../sfwork", "cd ../sfwork",
        "calibrate light -dark=../masters/dark_master -cc=dark 3 3 -cfa "
        "-debayer", "close",
    ])
    rm_glob(sfwork, "light_", keep_seq=False)
    run_script(S, W, "sf_g1b", [
        "requires 1.4.0", "set16bits", "setcompress 0", "cd work/sfwork",
        "set32bits", "stack pp_light med -norm=mul -out=selfflat_med",
        "set16bits", "seqsubsky pp_light 1", "close",
    ], os.path.join(sfwork, "selfflat_med.fit"))
    for tool, argv in (
        ("selfflat V1", [os.path.join(_libdir, "stack", "selfflat.py"),
                         os.path.join(sfwork, "selfflat_med.fit"),
                         os.path.join(sfwork, "selfflat_gain1.fit")]),
        ("rechroma", [os.path.join(_libdir, "stack", "rechroma.py"),
                      sfwork, str(len(subset))]),
    ):
        p = subprocess.run([sys.executable] + argv)
        if p.returncode != 0:
            sys.exit(f"{tool} failed")
    shutil.copy(os.path.join(sfwork, "selfflat_levels.json"),
                os.path.join(sfwork, "levels_v1.json"))
    rm_glob(sfwork, "pp_light_", keep_seq=False)
    run_script(S, W, "sf_g2", [
        "requires 1.4.0", "set16bits", "setcompress 0", "cd work/sfwork",
        "set32bits", "stack bkg_pp_light med -nonorm -out=selfflat_med2",
        "close",
    ], os.path.join(sfwork, "selfflat_med2.fit"))
    p = subprocess.run([sys.executable,
                        os.path.join(_libdir, "stack", "selfflat.py"),
                        os.path.join(sfwork, "selfflat_med2.fit"), gain])
    if p.returncode != 0:
        sys.exit("selfflat V2 fit failed")
    # the V2 fit just wrote V2-based levels beside the gain; the binding
    # levels for per-partition rechroma are the V1 ones (see docstring)
    shutil.copy(os.path.join(sfwork, "levels_v1.json"), levels)
    print("self-flat: masters/selfflat_gain.fit (V2 divisor) + V1 levels "
          "pinned for partition rechroma", flush=True)
    shutil.rmtree(sfstage)
    shutil.rmtree(sfwork)


def plan_partitions(names, exclude, ref_n, part_max):
    """Time-contiguous, size-balanced partitions over the KEPT frames; the
    pinned reference is staged (prepended) into every partition that does
    not naturally contain it, and excluded from those partitions' stacks."""
    kept = [n for n in range(1, len(names) + 1) if n not in exclude]
    if ref_n in exclude:
        sys.exit(f"--ref {ref_n} is in the exclude list")
    n_parts = max(1, -(-len(kept) // part_max))
    bounds = np.linspace(0, len(kept), n_parts + 1).round().astype(int)
    parts = []
    for i in range(n_parts):
        chunk = kept[bounds[i]:bounds[i + 1]]
        ref_home = ref_n in chunk
        parts.append({
            "part": i + 1,
            "orig": chunk,            # frames whose photons this stack keeps
            "staged": chunk if ref_home else [ref_n] + chunk,
            "ref_home": ref_home,
        })
    return parts


def stage_partition(S, W, set_name, names, part):
    d = os.path.join(W, "pstage")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    # staging order must equal sorted-filename order or position mapping
    # breaks: staged is sorted by n except a prepended ref, and the ref
    # COPY must sort first — prefix it so siril's sorted convert keeps
    # position 1 for it.
    for n in part["staged"]:
        src = os.path.join(S, set_name, names[n - 1])
        if not part["ref_home"] and n == part["staged"][0]:
            dst = os.path.join(d, "0REF_" + names[n - 1])
        else:
            dst = os.path.join(d, names[n - 1])
        os.symlink(src, dst)
    return d


def harvest_regdata(seq_path, part, names):
    """Per-frame records from the partition's registered .seq regdata,
    mapped back to original n. A zeroed row = match failure (siril leaves
    failed frames without registration data)."""
    seq = parse_seq_regdata(seq_path)
    if seq is None:
        return None
    layer = sorted(seq["layers"], key=lambda k: (k != "1", k))[0]
    rows = seq["layers"][layer]
    recs = []
    for pos, n in enumerate(part["staged"], start=1):
        if pos - 1 >= len(rows):
            break
        r = rows[pos - 1]
        registered = any(abs(v) > 0 for v in
                         (r["fwhm"], r["bg"], float(r["nstars"])))
        is_ref_copy = (not part["ref_home"]) and pos == 1
        recs.append({
            "n": n, "file": names[n - 1], "part": part["part"], "pos": pos,
            "ref_copy": is_ref_copy, "registered": bool(registered),
            "fwhm": r["fwhm"], "wfwhm": r["wfwhm"], "round": r["round"],
            "bg": r["bg"], "nstars": r["nstars"],
            "dx": r["H"][2], "dy": r["H"][5],
        })
    return recs


def verify_partition(rseq_path, part):
    """From the stacked r_ sequence: exactly the ref copy deselected in
    prepended-ref partitions (file numbers, not positions), everything
    else that registered selected."""
    seq = parse_seq_regdata(rseq_path)
    if seq is None:
        return None, "r_ seq unparseable"
    inc = dict(seq["images"])
    if not part["ref_home"]:
        if inc.get(1, 1) != 0:
            return None, f"staged ref (file 1) not deselected: {inc.get(1)}"
        wrong = [f for f, v in inc.items() if v == 0 and f != 1]
    else:
        wrong = [f for f, v in inc.items() if v == 0]
    if wrong:
        return None, f"unexpected deselections: {wrong}"
    stacked = sum(v for f, v in inc.items())
    return stacked, None


def partition_stages(route, ref_pos, exclude_ref, out_name):
    """Per-partition siril stages as (name, lines, rm_prefix) tuples, in
    order; rm_prefix names the sequence whose FRAMES die once the stage
    ran (its .seq survives for the QA harvest). Compression states follow
    the consumers: rechroma/selfflat parse plain FITS, so what they read
    is written uncompressed; everything siril-only is rice-compressed."""
    seq = "pp_light" if route == "flat" else "pp_bkg_pp_light"
    stackpol = "-filter-incl " if exclude_ref else ""
    # the staged reference copy is registration target only: its photons
    # belong to its home partition. unselect position 1 is gap-safe
    # (file 1's position is 1 regardless of later dropouts).
    unsel = [f"unselect r_{seq} 1 1"] if exclude_ref else []
    if route == "flat":
        return [
            ("s1", ["requires 1.4.0", "set16bits",
                    "setcompress 1 -type=rice 16", "cd work/pstage",
                    "convert light -out=../pwork", "cd ../pwork",
                    "calibrate light -dark=../masters/dark_master "
                    "-flat=../masters/flat_master -cc=dark 3 3 -cfa "
                    "-equalize_cfa -debayer", "close"], "light_"),
            ("s2", ["requires 1.4.0", "set16bits",
                    "setcompress 1 -type=rice 16", "cd work/pwork",
                    "setfindstar -sigma=0.5", f"setref {seq} {ref_pos}",
                    f"register {seq}", "close"], None),
            ("s3", ["requires 1.4.0", "set16bits", "setcompress 0",
                    "set32bits", "cd work/pwork"] + unsel +
                   [f"stack r_{seq} rej 3 3 {stackpol}-norm=addscale "
                    f"-out=../pstacks/{out_name}",
                    f"load ../pstacks/{out_name}", "stat", "close"],
             seq + "_"),
        ], seq
    # selfflat: calibrate (dark only) -> planar glow subtraction ->
    # rechroma (python, between stages) -> divide by the shared V2 gain ->
    # register -> stack. Faithful to the branch templates; bkg frames are
    # uncompressed for rechroma's plain-FITS parser.
    return [
        ("s1", ["requires 1.4.0", "set16bits",
                "setcompress 1 -type=rice 16", "cd work/pstage",
                "convert light -out=../pwork", "cd ../pwork",
                "calibrate light -dark=../masters/dark_master "
                "-cc=dark 3 3 -cfa -debayer", "close"], "light_"),
        ("s2", ["requires 1.4.0", "set16bits", "setcompress 0",
                "cd work/pwork", "seqsubsky pp_light 1", "close"],
         "pp_light_"),
        ("rechroma", None, None),
        ("s3", ["requires 1.4.0", "set16bits",
                "setcompress 1 -type=rice 16", "cd work/pwork",
                "calibrate bkg_pp_light -flat=../masters/selfflat_gain",
                "close"], "bkg_pp_light_"),
        ("s4", ["requires 1.4.0", "set16bits",
                "setcompress 1 -type=rice 16", "cd work/pwork",
                "setfindstar -sigma=0.5", f"setref {seq} {ref_pos}",
                f"register {seq}", "setcompress 0", "set32bits"] + unsel +
               [f"stack r_{seq} rej 3 3 {stackpol}-norm=addscale "
                f"-out=../pstacks/{out_name}",
                f"load ../pstacks/{out_name}", "stat", "close"],
         seq + "_"),
    ], seq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("set_name")
    ap.add_argument("--ref", type=int, required=True,
                    help="pinned reference frame n (sorted-raw index, "
                         "pick a measured-clean frame)")
    ap.add_argument("--route", required=True, choices=("flat", "selfflat"))
    ap.add_argument("--part-size", type=int, default=14)
    ap.add_argument("--exclude", default="",
                    help="comma-separated original frame n to exclude "
                         "(the recipe stack-block policy, applied at "
                         "staging)")
    ap.add_argument("--gain-subset", default="",
                    help="selfflat route: comma-separated frame n for the "
                         "gain-estimation median (default: 16 evenly over "
                         "the kept frames; pass measured-CLEAR frames on "
                         "a cloud-affected set)")
    ap.add_argument("--variant", default="e0",
                    help="tag for outputs (results/stack_<set>_<variant>)")
    ap.add_argument("--resume", action="store_true",
                    help="skip partitions already accumulated")
    ap.add_argument("--masters-only", action="store_true")
    args = ap.parse_args()

    S = os.path.join(_repo, args.session)
    W = os.path.join(S, "work")
    set_dir = os.path.join(S, args.set_name)
    if not os.path.isdir(set_dir):
        sys.exit(f"missing {set_dir}")
    os.makedirs(W, exist_ok=True)

    names = raw_list(set_dir)
    exclude = sorted({int(x) for x in args.exclude.split(",") if x.strip()})
    bad = [n for n in exclude if not 1 <= n <= len(names)]
    if bad:
        sys.exit(f"exclude out of range: {bad}")

    print(f"partitioned integration ({args.route}): "
          f"{args.session}/{args.set_name} — {len(names)} frames, exclude "
          f"{len(exclude)} ({exclude if exclude else 'none'}), variant "
          f"{args.variant}, ref n={args.ref} ({names[args.ref - 1]}), "
          f"part max {args.part_size}", flush=True)

    dark_med = build_master_dark(S, W)
    if args.route == "flat":
        build_master_flat(S, W, dark_med)
    else:
        if args.gain_subset:
            subset = sorted({int(x) for x in args.gain_subset.split(",")})
        else:
            kept = [n for n in range(1, len(names) + 1)
                    if n not in set(exclude)]
            subset = [kept[i] for i in
                      np.linspace(0, len(kept) - 1, 16).round().astype(int)]
        print(f"gain subset ({len(subset)}): {subset}", flush=True)
        build_selfflat_gain(S, W, args.set_name, names, subset)
    if args.masters_only:
        return

    parts = plan_partitions(names, set(exclude), args.ref, args.part_size)
    pstacks = os.path.join(W, "pstacks")
    os.makedirs(pstacks, exist_ok=True)
    qa_dir = os.path.join(W, "frameqa")
    os.makedirs(qa_dir, exist_ok=True)
    rec_path = os.path.join(qa_dir, f"records_{args.variant}.jsonl")
    state_path = os.path.join(qa_dir, f"combine_{args.variant}.json")
    sum_path = os.path.join(qa_dir, f"sum_{args.variant}.npy")
    cards_ref = os.path.join(qa_dir, f"cards_{args.variant}.fit")

    state = {"done": [], "weights": {}, "medians": {}, "reg": {},
             "staged": {}}
    if args.resume and os.path.isfile(state_path):
        state = json.load(open(state_path))
    elif os.path.exists(rec_path):
        os.remove(rec_path)

    acc = None
    if os.path.isfile(sum_path) and state["done"]:
        acc = np.lib.format.open_memmap(sum_path, mode="r+")

    for part in parts:
        out_name = f"part_{args.variant}_{part['part']:05d}"
        out_fit = os.path.join(pstacks, out_name + ".fit")
        n_staged = len(part["staged"])
        n_keep = len(part["orig"])
        if part["part"] in state["done"]:
            print(f"--- partition {part['part']}/{len(parts)}: already "
                  f"accumulated, skipping (resume)", flush=True)
            continue
        print(f"--- partition {part['part']}/{len(parts)}: frames "
              f"n={part['orig'][0]}..{part['orig'][-1]} ({n_keep} kept"
              f"{'' if part['ref_home'] else ' + staged ref'})", flush=True)
        stage_partition(S, W, args.set_name, names, part)
        pwork = os.path.join(W, "pwork")
        shutil.rmtree(pwork, ignore_errors=True)
        os.makedirs(pwork)
        ref_pos = (part["orig"].index(args.ref) + 1 if part["ref_home"]
                   else 1)
        stages, seq = partition_stages(
            args.route, ref_pos, not part["ref_home"], out_name)
        reg_log = None
        for sname, lines, rmpfx in stages:
            tag = f"p{args.variant}_{part['part']:02d}_{sname}"
            if sname == "rechroma":
                shutil.copy(os.path.join(W, "masters",
                                         "selfflat_levels.json"),
                            os.path.join(pwork, "selfflat_levels.json"))
                p = subprocess.run(
                    [sys.executable,
                     os.path.join(_libdir, "stack", "rechroma.py"),
                     pwork, str(n_staged)])
                if p.returncode != 0:
                    sys.exit(f"partition {part['part']} rechroma failed")
                continue
            expect = out_fit if f"stack r_{seq}" in " ".join(lines) else None
            log = run_script(S, W, tag, lines, expect)
            if f"register {seq}" in " ".join(lines):
                reg_log = log
            if rmpfx:
                rm_glob(pwork, rmpfx)
        tot = reg_total(reg_log) if reg_log else None
        recs = harvest_regdata(os.path.join(pwork, seq + "_.seq"),
                               part, names)
        if recs is None:
            sys.exit(f"partition {part['part']}: {seq}_.seq regdata "
                     f"unparseable — refusing to continue without frame QA")
        stacked, err = verify_partition(
            os.path.join(pwork, "r_" + seq + "_.seq"), part)
        if err:
            os.remove(out_fit)
            sys.exit(f"partition {part['part']} exclusion verify FAILED "
                     f"({err}) — stack removed")
        with open(rec_path, "a") as f:
            for r in recs:
                f.write(json.dumps(r) + "\n")
        reg_n = sum(1 for r in recs if r["registered"] and not r["ref_copy"])
        med = stat_median(log)
        # incremental combine: weight = frames actually stacked; only one
        # partition stack ever exists on disk
        cards, planes, _ = am.read_fits_planes(out_fit)
        if acc is None:
            acc = np.lib.format.open_memmap(
                sum_path, mode="w+", dtype=np.float64, shape=planes.shape)
            acc[:] = 0.0
        acc += planes.astype(np.float64) * stacked
        acc.flush()
        if not os.path.isfile(cards_ref):
            shutil.copy(out_fit, cards_ref)
        os.remove(out_fit)
        state["done"].append(part["part"])
        state["weights"][str(part["part"])] = stacked
        if med is not None:
            state["medians"][str(part["part"])] = med
        state["reg"][str(part["part"])] = reg_n
        state["staged"][str(part["part"])] = n_keep
        json.dump(state, open(state_path, "w"))
        if tot:
            print(f"    registered {tot[1]}/{n_staged} staged; kept-frame "
                  f"regs {reg_n}/{n_keep}; stacked {stacked}; "
                  f"stack G median {med}", flush=True)
        if reg_n * 10 < n_keep * 9:
            print(f"    WARNING: partition registration {reg_n}/{n_keep} "
                  f"< 0.9 (inspection-grade advisory)", flush=True)
        shutil.copy(os.path.join(pwork, seq + "_.seq"),
                    os.path.join(qa_dir,
                                 f"seq_{args.variant}_p{part['part']:02d}.seq"))
        shutil.rmtree(pwork)
        shutil.rmtree(os.path.join(W, "pstage"))

    total_reg = sum(state["reg"].values())
    total_staged = sum(state["staged"].values())
    total_w = sum(state["weights"].values())
    if total_staged and total_reg * 2 < total_staged:
        sys.exit(f"registration floor: {total_reg}/{total_staged} kept "
                 f"frames registered — less than half the set (see "
                 f"run_pipeline reg_floor rationale)")
    meds = [state["medians"][k] for k in sorted(state["medians"])]
    if meds:
        spread = (max(meds) - min(meds)) / max(np.median(meds), 1)
        print(f"partition stack G medians: {meds} (spread "
              f"{100 * spread:.2f}% — addscale normalization consistency "
              f"check{'' if spread < 0.02 else ': WARNING, expected <2%'})",
              flush=True)

    # final: frame-count-weighted mean of the aligned partition stacks,
    # float64 accumulation -> float32 in the [0,1] ushort convention (the
    # scale the downstream chain reads; partition stacks skipped
    # -output_norm so this single division is the only rescale)
    cards, _, _ = am.read_fits_planes(cards_ref)
    final = (np.asarray(acc) / total_w).astype(np.float32)
    out_stack = os.path.join(S, "results",
                             f"stack_{args.set_name}_{args.variant}.fit")
    os.makedirs(os.path.join(S, "results"), exist_ok=True)
    am.write_fits_planes(out_stack, cards, final)
    for p in (sum_path, cards_ref):
        os.remove(p)
    print(f"DONE: {out_stack}\n  kept-frame registrations {total_reg}/"
          f"{total_staged}; combined weight {total_w} frames over "
          f"{len(parts)} partitions; frame records {rec_path}", flush=True)


if __name__ == "__main__":
    main()
