#!/usr/bin/env python3
"""Run siril SPCC on a plate-solved stack and CAPTURE the K factors.

Usage: spcc_run.py <session> <set> [--in=<fits>] [--out=<fits>]
                   [--catalog=localgaia]

SPCC's measured white-balance factors (K per channel) are printed only in
siril's log; they record what the raw stack's balance actually was (the raw
G channel runs ~1.5x hot: K G 0.656 vs R 1.000 on the reference stack, 509
kept stars, the Bayer imbalance) and are the first thing to compare when a
new stack of the same sky calibrates differently. This runner captures them
so they survive: the full siril log lands in work/spcc_<set>.log and the
parsed factors + stack identity in work/spcc_<set>.json.

Defaults: in results/stack_<set>_wcs.fit, out results/stack_<set>_spcc.fit
(override both for non-default stems like stack_set-03_norgbeq_*).
The generated .ssf lives under work/ — the siril flatpak has its own
private /tmp, so scripts must stay under $HOME.

Exits nonzero if SPCC ran but no K factors could be parsed (the log
file then holds whatever siril actually said).
"""
import json
import os
import re
import subprocess
import sys
import time

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    session, set_name = args
    sdir = os.path.abspath(session)
    catalog = opts.get("catalog", "localgaia")
    p_in = os.path.join(sdir, opts.get("in", f"results/stack_{set_name}_wcs.fit"))
    p_out = os.path.join(sdir, opts.get("out", f"results/stack_{set_name}_spcc.fit"))
    if not os.path.exists(p_in):
        sys.exit(f"spcc_run: no input {p_in} (plate-solve first: "
                 "solve_field.py --inject)")
    work = os.path.join(sdir, "work")
    os.makedirs(work, exist_ok=True)

    rel_in = os.path.relpath(p_in, sdir)
    rel_out = os.path.relpath(p_out, sdir)
    ssf = os.path.join(work, f"spcc_{set_name}.gen.ssf")
    with open(ssf, "w") as f:
        f.write("requires 1.4.0\n"
                f"load {rel_in[:-4] if rel_in.endswith('.fit') else rel_in}\n"
                f"spcc -catalog={catalog}\n"
                f"save {rel_out[:-4] if rel_out.endswith('.fit') else rel_out}\n"
                "close\n")
    print(f"[spcc_run] {rel_in} -> {rel_out} (catalog {catalog})")
    r = subprocess.run(SIRIL + ["-d", sdir, "-s", ssf],
                       capture_output=True, text=True)
    log = r.stdout + ("\n--- stderr ---\n" + r.stderr if r.stderr else "")
    p_log = os.path.join(work, f"spcc_{set_name}.log")
    with open(p_log, "w") as f:
        f.write(log)
    if r.returncode != 0 or not os.path.exists(p_out):
        sys.exit(f"spcc_run: siril failed (log: {p_log})\n" + log[-1500:])

    # siril 1.4.4 prints the white-balance factors per channel index
    # ("log: K0: 1.000") and the background offsets ("log: B0:
    # +2.27871e-03"); channels 0/1/2 = R/G/B. Photometry scope: total
    # from "Applying aperture photometry to N stars", kept = total
    # minus border rejects minus per-star failures.
    ks, bs = {}, {}
    for idx, ch in enumerate("RGB"):
        m = re.search(rf"\bK{idx}\s*[:=]\s*([0-9]+\.?[0-9]*)", log)
        if m:
            ks[ch] = float(m.group(1))
        m = re.search(rf"\bB{idx}\s*[:=]\s*([+-]?[0-9.eE+-]+)", log)
        if m:
            bs[ch] = float(m.group(1))
    m_phot = re.search(r"aperture photometry to (\d+) stars", log)
    n_phot = int(m_phot.group(1)) if m_phot else None
    n_kept = (n_phot - len(re.findall(r"is outside image", log))
              - len(re.findall(r"photometry failed", log))
              if n_phot else None)
    st = os.stat(p_in)
    rec = {"set": set_name, "catalog": catalog,
           "input": rel_in, "output": rel_out,
           "input_size": st.st_size, "input_mtime": int(st.st_mtime),
           "k_factors": ks or None, "b_offsets": bs or None,
           "n_photometry": n_phot, "n_kept": n_kept,
           "date": time.strftime("%Y-%m-%d %H:%M:%S")}
    p_json = os.path.join(work, f"spcc_{set_name}.json")
    with open(p_json, "w") as f:
        json.dump(rec, f, indent=1)
    if not ks:
        sys.exit(f"spcc_run: SPCC ran but no K factors parsed — READ THE "
                 f"LOG ({p_log}) and fix the pattern; the factors are the "
                 "point of this runner")
    print(f"[spcc_run] K factors: " +
          " ".join(f"{c} {v:.3f}" for c, v in ks.items()) +
          (f" ({rec['n_kept']}/{rec['n_photometry']} stars kept)"
           if rec["n_kept"] else "") +
          f" -> {os.path.relpath(p_json, sdir)}")


if __name__ == "__main__":
    main()
