#!/usr/bin/env python3
"""Run siril SPCC on a plate-solved stack and CAPTURE the K factors.

Usage: spcc_run.py <session> <set> [--in=<fits>] [--out=<fits>]
                   [--catalog=localgaia] [--tag=<suffix>]
                   [--oscsensor=<name>] [--oscfilter=<name>]
                   [--whiteref=<name>]
                   [--narrowband=true --rwl=<nm> --gwl=<nm> --bwl=<nm>
                    [--rbw/--gbw/--bbw=<nm>]]

SPCC's measured white-balance factors (K per channel) are printed only in
siril's log; they record what the raw stack's balance actually was (a raw
OSC stack's G channel runs hot — the Bayer imbalance — so K G sits well
below R) and are the first thing to compare when a
new stack of the same sky calibrates differently. This runner captures them
so they survive: the full siril log lands in work/spcc_<set>.log and the
parsed factors + stack identity in work/spcc_<set>.json (--tag suffixes
both, so an experiment run never overwrites the set's canonical record).

The sensor/filter/white-reference spec resolves CLI > recipe > sensor-null
and the provenance is printed. `datasets/<session>/<set>/recipe.json` may
carry {"spcc": {"oscsensor": ..., "oscfilter": ..., "whiteref": ...}};
names must match `spcc_list` entries (quote names with spaces on the CLI).
With no spec anywhere, SPCC fits Gaia star colours against siril's default
response — the generic sensor-null calibration (measured on the one chip
with a database curve: grounding moves K <=1.5% and the output <=2.6e-4
p99, so null is the adequate default; measurement detail in git history).

Defaults: in/out = <repo>/web/results/<session>/stack_<set>_{wcs,spcc}.fit (the
project-root results tree); a COMPOSED target whose plain stem is absent
defaults to its stack_<set>_comp_{wcs,spcc}.fit family. An explicit
--in/--out resolves against the CWD or an absolute path; override both for
non-default stems like stack_<set>_norgbeq_*.
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

SIRIL = ["flatpak", "run", "--command=siril-cli", "org.siril.Siril"]

NAME_KEYS = ("oscsensor", "oscfilter", "whiteref")   # database names (quoted)
NB_KEYS = ("narrowband", "rwl", "gwl", "bwl",        # narrowband mode: flag +
           "rbw", "gbw", "bbw")                      # wavelengths/bandwidths
SPEC_KEYS = NAME_KEYS + NB_KEYS


def resolve_spec(opts, session, set_name):
    """SPCC spec per key: CLI > recipe.json "spcc" > none. Returns
    ({key: value}, {key: source}) with only the keys that resolved."""
    repo = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    p_recipe = os.path.join(repo, "datasets", os.path.basename(
        os.path.normpath(session)), set_name, "recipe.json")
    recipe = {}
    if os.path.exists(p_recipe):
        with open(p_recipe) as f:
            recipe = json.load(f).get("spcc", {})
    spec, prov = {}, {}
    for k in SPEC_KEYS:
        if k in opts:
            spec[k], prov[k] = opts[k], "cli"
        elif k in recipe:
            spec[k], prov[k] = recipe[k], "recipe"
    return spec, prov


def spcc_extra_args(spec):
    """Spec dict -> siril `spcc` argument string. Database names are
    quoted (spaces); `narrowband` is a bare flag; wavelengths/bandwidths
    are plain numerics."""
    parts = []
    for k in NAME_KEYS:
        if k in spec:
            parts.append(f'"-{k}={spec[k]}"')
    if spec.get("narrowband") in (True, "true", "1", 1):
        parts.append("-narrowband")
    for k in NB_KEYS[1:]:
        if k in spec:
            parts.append(f"-{k}={spec[k]}")
    return "".join(" " + p for p in parts)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    session, set_name = args
    sdir = os.path.abspath(session)
    catalog = opts.get("catalog", "localgaia")
    spec, spec_prov = resolve_spec(opts, session, set_name)
    # Derived stacks live at the web-servable output root web/results/<session>/
    # (not under the transient session tree). Default in/out point there; an
    # explicit --in/--out resolves against the CWD (or an absolute path), never
    # joined onto the session dir — which double-prefixed a repo-relative path
    # into an unfindable one.
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    results = os.path.join(repo, "web", "results",
                           os.path.basename(os.path.normpath(session)))
    p_in = (os.path.abspath(opts["in"]) if "in" in opts
            else os.path.join(results, f"stack_{set_name}_wcs.fit"))
    p_out = (os.path.abspath(opts["out"]) if "out" in opts
             else os.path.join(results, f"stack_{set_name}_spcc.fit"))
    # a COMPOSED virtual target's product carries the _comp stem
    # (compose.py writes stack_<target>_comp.fit): when the plain stem is
    # absent and the composed one is solved, default to it — output too,
    # so the product family stays stack_<target>_comp_{wcs,spcc}.fit
    if ("in" not in opts and not os.path.exists(p_in)
            and os.path.exists(os.path.join(
                results, f"stack_{set_name}_comp_wcs.fit"))):
        p_in = os.path.join(results, f"stack_{set_name}_comp_wcs.fit")
        if "out" not in opts:
            p_out = os.path.join(results,
                                 f"stack_{set_name}_comp_spcc.fit")
        print("[spcc_run] composed target — defaulting to the _comp stems")
    if not os.path.exists(p_in):
        sys.exit(f"spcc_run: no input {p_in} (plate-solve first: "
                 "solve_field.py --inject)")
    # SPCC is BROADBAND-only: a mono stack has no colour to calibrate
    # (Siril refuses with "command is not for monochrome images") — refuse
    # up front with the mechanism instead of four commands into a siril run
    from astropy.io import fits as _fits
    if int(_fits.getheader(p_in).get("NAXIS3", 1)) < 3:
        sys.exit(f"spcc_run: {os.path.basename(p_in)} is MONOCHROME — SPCC "
                 "is broadband-only (no colour to calibrate). A mono/"
                 "single-filter stack finishes luminance-only "
                 "(finish_render skips SPCC for it); colour comes from the "
                 "composed target (compose_channels).")
    work = os.path.join(sdir, "work")
    os.makedirs(work, exist_ok=True)

    tag = f"_{opts['tag']}" if opts.get("tag") else ""
    spcc_args = f"-catalog={catalog}" + spcc_extra_args(spec)
    rel_in = os.path.relpath(p_in, sdir)
    rel_out = os.path.relpath(p_out, sdir)
    ssf = os.path.join(work, f"spcc_{set_name}{tag}.gen.ssf")
    with open(ssf, "w") as f:
        # setcompress is a PERSISTED siril preference (config.ini), not
        # per-script state — pin it off or the save inherits whatever the
        # last session left and writes .fit.fz where the record expects .fit
        f.write("requires 1.4.0\n"
                "setcompress 0\n"
                f"load {rel_in[:-4] if rel_in.endswith('.fit') else rel_in}\n"
                f"spcc {spcc_args}\n"
                f"save {rel_out[:-4] if rel_out.endswith('.fit') else rel_out}\n"
                "close\n")
    print(f"[spcc_run] {rel_in} -> {rel_out} (catalog {catalog})")
    print("[spcc_run] sensor spec: " + (" ".join(
        f"{k}='{spec[k]}' ({spec_prov[k]})" for k in SPEC_KEYS if k in spec)
        or "sensor-null (generic default)"))
    r = subprocess.run(SIRIL + ["-d", sdir, "-s", ssf],
                       capture_output=True, text=True)
    log = r.stdout + ("\n--- stderr ---\n" + r.stderr if r.stderr else "")
    p_log = os.path.join(work, f"spcc_{set_name}{tag}.log")
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
           "sensor_spec": {k: spec[k] for k in SPEC_KEYS if k in spec} or None,
           "sensor_spec_source": spec_prov or None,
           "input": rel_in, "output": rel_out,
           "input_size": st.st_size, "input_mtime": int(st.st_mtime),
           "k_factors": ks or None, "b_offsets": bs or None,
           "n_photometry": n_phot, "n_kept": n_kept}
    # the K record is a per-set TOOL MEASURE — its versioned home is the
    # tracked datasets qa_work (the siril log stays session-work scratch)
    qa = os.path.join(repo, "datasets", os.path.basename(
        os.path.normpath(session)), set_name, "qa_work")
    os.makedirs(qa, exist_ok=True)
    p_json = os.path.join(qa, f"spcc_{set_name}{tag}.json")
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
          f" -> {os.path.relpath(p_json, repo)}")


if __name__ == "__main__":
    main()
