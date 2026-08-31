#!/usr/bin/env python3
"""Run siril SPCC on a plate-solved stack and CAPTURE the K factors.

Usage: spcc_run.py <session> <set> [--in=<fits>] [--out=<fits>]
                   [--catalog=localgaia] [--tag=<suffix>]
                   [--oscsensor=<name>] [--oscfilter=<name>]
                   [--osclpf=<name>] [--whiteref=<name>]
                   [--narrowband=true --rwl=<nm> --gwl=<nm> --bwl=<nm>
                    [--rbw/--gbw/--bbw=<nm>]]
       spcc_run.py --selftest        (data-free: the refusal, preflight and
                                      log-order rules on planted text)

SPCC's measured white-balance factors (K per channel) are printed only in
siril's log; they record what the raw stack's balance actually was (a raw
OSC stack's G channel runs hot — the Bayer imbalance — so K G sits well
below R) and are the first thing to compare when a
new stack of the same sky calibrates differently. This runner captures them
so they survive: the siril log lands in work/spcc_<set>.log and the parsed
factors + stack identity in datasets/<session>/<set>/qa_work/spcc_<set>.json
(--tag suffixes both, AND the product: with --tag and no --out the product
defaults to stack_<set>_<tag>_spcc.fit (a composed target: stack_<set>_comp_
<tag>_spcc.fit), so a tagged run never overwrites the canonical product; an
explicit --out still wins).

The sensor/filter/white-reference spec resolves CLI > recipe.json and the
provenance is printed and recorded. `datasets/<session>/<set>/recipe.json`
may carry {"spcc": {"oscsensor": ..., "oscfilter": ..., "osclpf": ...,
"whiteref": ...}}; names must be `spcc_list` entries. A NAMED oscsensor is
REQUIRED — a spec-less run is refused before Siril. Measured mechanism
(datasets/july31/set-01/qa_work/spcc_h0_probe.json, the H0 probe;
docs/spcc-sensor-curve-z6iii.md section 1.2): headless Siril 1.4.4 resolves
the sensor/filter/white-reference names BEFORE loading its database, so a run
with no name resolved to index 0 of every list — "Generic mono sensor" x
Antlia R/G/B — and every shipped K record came from that accidental model
(the shipped log prints `SPCC will use mono senor "(null)"` at line 52 and
`SPCC JSON metadata loaded` at 53). With `spcc_list oscsensor` run first the
metadata is loaded before `spcc` resolves: "Nikon D750" gave K
1.000/0.697/0.945 and "Nikon D500" 1.000/0.700/0.955 on the same input where
the index-0 run gave 1.000/0.687/0.927, and the spec-less arm errored with
Siril's own "Either the sensor or a filter was not specified ..." (exit 1, no
K). So the generated .ssf runs `spcc_list oscsensor` before `spcc`, the
oscfilter/whiteref defaults are passed EXPLICITLY ("No filter", "Average
Spiral Galaxy" — Siril's "previously used value" path is never relied on), the
model is preflighted against the database on disk (it must exist as an
OSC_SENSOR; an `is_dslr` model needs `-osclpf=` naming an LPF entry, e.g.
"Full spectrum (no filter)", or Siril NULL-derefs — the exit-139 family), and
the captured log is asserted: metadata loaded before `SPCC will use`, the
model listed by spcc_list, the model echoed by spcc. A failed assertion exits
non-zero, writes NO record and REMOVES the product Siril wrote (the chain's
finish only tests the product's existence, so an unverified product left on
disk would be stretched into a judge surface); the log stays.

REMOVAL CONDITION: retire the spcc_list-first preload + the log-order
assertion when Siril loads the SPCC metadata before resolving names in do_pcc
(1.4.4 resolves at command.c:10152-10188 and loads at :10205; upstream master
ee7b942 still resolves first) — re-check at every version bump (BACKLOG
siril-1.5).

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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from siril_run import SIRIL, run as siril_run   # serialized invoker

NAME_KEYS = ("oscsensor", "oscfilter", "osclpf", "whiteref")   # database names (quoted)
NB_KEYS = ("narrowband", "rwl", "gwl", "bwl",        # narrowband mode: flag +
           "rbw", "gbw", "bbw")                      # wavelengths/bandwidths
SPEC_KEYS = NAME_KEYS + NB_KEYS
EXPLICIT_DEFAULTS = {"oscfilter": "No filter", "whiteref": "Average Spiral Galaxy"}
SPCC_DB = os.environ.get("SPCC_DB", os.path.expanduser(
    "~/.var/app/org.siril.Siril/data/siril-spcc-database"))
MECHANISM = ("headless Siril 1.4.4 resolves sensor/filter/white-reference names "
             "BEFORE loading its database, so a spec-less run applied index 0 of "
             "each list — \"Generic mono sensor\" x Antlia R/G/B — MEASURED, "
             "datasets/july31/set-01/qa_work/spcc_h0_probe.json (H0: with the "
             "preload, \"Nikon D750\" K 1.000/0.697/0.945 and \"Nikon D500\" "
             "1.000/0.700/0.955 vs the index-0 1.000/0.687/0.927 on the same "
             "input; the spec-less arm errors, exit 1, no K)")


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


def refuse_if_unnamed(spec):
    """The spec-less refusal (Siril's own contract, made loud before Siril
    runs): returns the message, or None when an oscsensor is named."""
    if spec.get("oscsensor"):
        return None
    return ("spcc_run: REFUSED — no oscsensor named (CLI or recipe): " + MECHANISM +
            ". Fix: recipe.json {\"spcc\": {\"oscsensor\": \"<a `spcc_list oscsensor` "
            "model string>\"}} or --oscsensor=<model>.")


def apply_explicit_defaults(spec, prov):
    """With an oscsensor named, pass oscfilter/whiteref EXPLICITLY when the
    spec leaves them out, recorded with source 'default-explicit' — never
    Siril's 'previously used value' path."""
    for k, v in EXPLICIT_DEFAULTS.items():
        if k not in spec:
            spec[k], prov[k] = v, "default-explicit"
    return spec, prov


def load_osc_sensors(db_root):
    """The loader's own walk (spcc_json.c:734-766): every *.json under the
    root except .git and names containing 'schema'. Returns {model: {"files":
    [...], "is_dslr": any channel object carries is_dslr true}} for the
    OSC_SENSOR objects — the flag is read from the JSON objects, never from
    the name (the loader propagates one channel's flag to all three)."""
    models = {}
    for dp, dn, fn in os.walk(db_root):
        dn[:] = [d for d in dn if d != ".git"]
        for f in fn:
            if not f.endswith(".json") or "schema" in f:
                continue
            try:
                d = json.load(open(os.path.join(dp, f)))
            except (OSError, ValueError):
                continue
            for o in (d if isinstance(d, list) else [d]):
                if isinstance(o, dict) and o.get("type") == "OSC_SENSOR" and o.get("model"):
                    m = models.setdefault(o["model"], {"files": [], "is_dslr": False})
                    rel = os.path.relpath(os.path.join(dp, f), db_root)
                    if rel not in m["files"]:
                        m["files"].append(rel)
                    m["is_dslr"] = m["is_dslr"] or (o.get("is_dslr") is True)
    return models


def preflight_spec(spec, db_root=SPCC_DB):
    """The requested model must exist as an OSC_SENSOR in the database on
    disk, and an is_dslr model must name an -osclpf= (or Siril NULL-derefs:
    the exit-139 family). Returns (ok, message, model_info)."""
    model = spec.get("oscsensor")
    if not os.path.isdir(db_root):
        return False, (f"spcc_run: REFUSED — siril-spcc-database not found at {db_root} "
                       "(clone gitlab.com/free-astro/siril-spcc-database; without it SPCC "
                       "SEGFAULTS silently)"), None
    models = load_osc_sensors(db_root)
    if model not in models:
        return False, (f"spcc_run: REFUSED — oscsensor \"{model}\" is not an OSC_SENSOR "
                       f"`model` in the database at {db_root} ({len(models)} models; "
                       "`spcc_list oscsensor` prints them). Siril's own error for an "
                       "unknown name is the authority; this preflight only makes the "
                       "message better."), None
    info = models[model]
    if info["is_dslr"] and not spec.get("osclpf"):
        return False, (f"spcc_run: REFUSED — oscsensor \"{model}\" carries is_dslr: true "
                       f"(in {', '.join(info['files'])}; the loader propagates one channel's "
                       "flag to all three) and no osclpf is named: after the preload Siril "
                       "REQUIRES -osclpf= naming an existing LPF entry for a DSLR model, or "
                       "takes the NULL-deref path (exit 139). Name one exactly, e.g. "
                       "--osclpf=\"Full spectrum (no filter)\" (`spcc_list osclpf` prints "
                       "the entries)."), info
    return True, "", info


def check_log_resolution(log, model):
    """Post-run assertions on the captured Siril log: (a) `SPCC JSON metadata
    loaded` precedes `SPCC will use`; (b) the model appears verbatim as a
    `log: <model>` line inside the spcc_list block (after its 'OSC Sensors'
    header, before the use line); (c) the use line echoes the requested name.
    Returns (ok, {"loaded_line", "listed_line", "use_line", "problems"}) with
    1-based line numbers (None where absent)."""
    lines = log.splitlines()
    idx = lambda pred: next((i + 1 for i, l in enumerate(lines) if pred(l)), None)
    loaded = idx(lambda l: "SPCC JSON metadata loaded" in l)
    use = idx(lambda l: "SPCC will use" in l)
    header = idx(lambda l: l.strip() == "log: OSC Sensors")
    listed = None
    if header and use:
        listed = next((i + 1 for i, l in enumerate(lines)
                       if header <= i + 1 < use and l.strip() == f"log: {model}"), None)
    problems = []
    if not (loaded and use and loaded < use):
        problems.append(f"(a) metadata loaded (line {loaded}) does not precede "
                        f"'SPCC will use' (line {use})")
    if not listed:
        problems.append(f"(b) 'log: {model}' not found in the spcc_list block "
                        f"(header line {header}, use line {use})")
    if not (use and f'SPCC will use OSC sensor "{model}"' in lines[use - 1]):
        problems.append(f"(c) the use line does not echo \"{model}\": "
                        f"{lines[use - 1].strip() if use else None!r}")
    return (not problems), {"loaded_line": loaded, "listed_line": listed,
                            "use_line": use, "problems": problems}


def default_out(results, set_name, tag, composed=False):
    """The product path when --out is not given: canonical stack_<set>_spcc.fit
    (composed target: stack_<set>_comp_spcc.fit); with a --tag the product is
    tag-named — stack_<set>_<tag>_spcc.fit / stack_<set>_comp_<tag>_spcc.fit —
    so a tagged run never overwrites the canonical product."""
    stem = f"stack_{set_name}" + ("_comp" if composed else "") + (f"_{tag}" if tag else "")
    return os.path.join(results, f"{stem}_spcc.fit")


def discard_unverified(p_out):
    """The RESOLUTION-NOT-VERIFIED path: remove the product Siril wrote, so a
    finish that only tests the product's existence cannot stretch an
    unverified model into a judge surface. Returns True when a file was
    removed."""
    if os.path.exists(p_out):
        os.remove(p_out)
        return True
    return False


def spcc_extra_args(spec):
    """Spec dict -> siril `spcc` argument string. Database names are
    quoted whole-token ("-oscsensor=Nikon D750" — Siril's own help form, H0);
    `narrowband` is a bare flag; wavelengths/bandwidths are plain numerics."""
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


def selftest():
    """Data-free positive controls on planted text (every gate ships with a
    control that makes it fire): the log-order assertions, the spec-less
    refusal, and the is_dslr preflight against a planted database in a temp
    dir (never the real clone)."""
    import tempfile
    L = lambda *ls: "\n".join(ls) + "\n"
    listing = L("log: Running command: spcc_list", "SPCC JSON metadata loaded", "log: OSC Sensors",
                "log: Nikon D500", "log: Nikon D750", "End of command spcc_list")
    good = listing + L("log: Running command: spcc", 'log: SPCC will use OSC sensor "Nikon D750" and filter "No filter"',
                       "log: K0: 1.000", "log: K1: 0.697", "log: K2: 0.945")
    use_first = L("log: Running command: spcc", 'log: SPCC will use mono senor "(null)" and filters "(null)"',
                  "SPCC JSON metadata loaded", "log: K0: 1.000")
    absent = L("SPCC JSON metadata loaded", "log: OSC Sensors", "log: Nikon D500", "End of command spcc_list",
               'log: SPCC will use OSC sensor "Nikon D750" and filter "No filter"')
    with tempfile.TemporaryDirectory() as db:
        os.makedirs(os.path.join(db, "osc_sensors"))
        def plant(name, model, dslr_on):
            objs = [{"model": model, "name": f"{model} {c}", "type": "OSC_SENSOR", "channel": c,
                     "dataPoints": 1, "values": {"value": [1.0], "range": {"min": 400, "max": 700}}}
                    for c in ("RED", "GREEN", "BLUE")]
            if dslr_on is not None:
                objs[dslr_on]["is_dslr"] = True
            json.dump(objs, open(os.path.join(db, "osc_sensors", name), "w"))
        plant("Planted_DSLR.json", "Planted DSLR", 0)      # is_dslr on the RED object only
        plant("Planted_Mirrorless.json", "Planted Mirrorless", None)
        json.dump({"$schema": "x"}, open(os.path.join(db, "spcc-database-schema.json"), "w"))
        cases = [
            ("(i) use-before-load log -> assertion (a) fails",
             lambda: (lambda ok, d: (not ok) and any(p.startswith("(a)") for p in d["problems"]))(*check_log_resolution(use_first, "Nikon D750"))),
            ("(ii) load-before-use, model absent from the list block -> (b) fails",
             lambda: (lambda ok, d: (not ok) and any(p.startswith("(b)") for p in d["problems"]) and not any(p.startswith("(a)") for p in d["problems"]))(*check_log_resolution(absent, "Nikon D750"))),
            ("(iii) loaded, listed, echoed -> passes with line numbers",
             lambda: (lambda ok, d: ok and d["loaded_line"] == 2 and d["listed_line"] == 5 and d["use_line"] == 8)(*check_log_resolution(good, "Nikon D750"))),
            ("(iv) null spec -> refused before Siril (message names the mechanism)",
             lambda: (lambda m: m is not None and "REFUSED" in m and "index 0" in m and "spcc_h0_probe" in m)(refuse_if_unnamed({"oscfilter": "No filter"}))),
            ("(v) planted OSC_SENSOR with is_dslr on one channel, no osclpf -> refused by the preflight",
             lambda: (lambda ok, msg, info: (not ok) and "is_dslr" in msg and "Full spectrum (no filter)" in msg and info["is_dslr"])(*preflight_spec({"oscsensor": "Planted DSLR"}, db))),
            ("(v') the same model with --osclpf named -> passes the preflight",
             lambda: preflight_spec({"oscsensor": "Planted DSLR", "osclpf": "Full spectrum (no filter)"}, db)[0]),
            ("(v'') a model with no is_dslr -> passes; an unknown model -> refused",
             lambda: preflight_spec({"oscsensor": "Planted Mirrorless"}, db)[0] and not preflight_spec({"oscsensor": "Nikon Zz"}, db)[0]),
            ("(vi) explicit defaults recorded as default-explicit, a named value kept",
             lambda: apply_explicit_defaults({"oscsensor": "X", "whiteref": "W"}, {"oscsensor": "cli", "whiteref": "cli"}) == ({"oscsensor": "X", "whiteref": "W", "oscfilter": "No filter"}, {"oscsensor": "cli", "whiteref": "cli", "oscfilter": "default-explicit"})),
            ("(vii) a planted product at a temp p_out is REMOVED by the failure path (and a second call finds nothing)",
             lambda: (lambda pth: (open(pth, "w").write("x") and discard_unverified(pth) and not os.path.exists(pth) and not discard_unverified(pth)))(os.path.join(db, "planted_spcc.fit"))),
            ("(viii) default_out: no tag -> canonical; tag -> tag-named; composed + tag -> comp tag-named",
             lambda: (default_out("/r", "set-01", "") == "/r/stack_set-01_spcc.fit"
                      and default_out("/r", "set-01", "smoke_b") == "/r/stack_set-01_smoke_b_spcc.fit"
                      and default_out("/r", "set-01", "smoke_b", composed=True) == "/r/stack_set-01_comp_smoke_b_spcc.fit"
                      and default_out("/r", "set-01", None, composed=True) == "/r/stack_set-01_comp_spcc.fit")),
        ]
        bad = 0
        for label, fn in cases:
            try:
                ok = bool(fn())
            except Exception as ex:      # a crash is a WRONG, printed
                ok = False; label += f"  [{type(ex).__name__}: {ex}]"
            print(f"  selftest {'ok  ' if ok else 'WRONG'} {label}")
            bad |= not ok
    if bad:
        print("spcc_run --selftest: FAIL — a rule does not fire as stated")
        return 1
    print("OK: spcc_run rules — the log-order assertions (a)(b)(c) fire on planted "
          "text, the spec-less refusal fires before Siril, the is_dslr preflight "
          "refuses without an osclpf and passes with one, defaults are explicit, "
          "the failure path removes the product, a tagged run defaults to a "
          "tag-named product")
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        return selftest()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:]
                if a.startswith("--") and "=" in a)
    if len(args) != 2:
        sys.exit(__doc__)
    session, set_name = args
    sdir = os.path.abspath(session)
    catalog = opts.get("catalog", "localgaia")
    spec, spec_prov = resolve_spec(opts, session, set_name)
    # A named oscsensor is REQUIRED (the measured mechanism in the docstring):
    # refuse before Siril, no record written.
    msg = refuse_if_unnamed(spec)
    if msg:
        sys.exit(msg)
    spec, spec_prov = apply_explicit_defaults(spec, spec_prov)
    ok, msg, model_info = preflight_spec(spec)
    if not ok:
        sys.exit(msg)
    # Derived stacks live at the web-servable output root web/results/<session>/
    # (not under the transient session tree). Default in/out point there; an
    # explicit --in/--out resolves against the CWD (or an absolute path), never
    # joined onto the session dir — which double-prefixed a repo-relative path
    # into an unfindable one.
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    results = os.path.join(repo, "web", "results",
                           os.path.basename(os.path.normpath(session)))
    tag_raw = opts.get("tag") or ""
    p_in = (os.path.abspath(opts["in"]) if "in" in opts
            else os.path.join(results, f"stack_{set_name}_wcs.fit"))
    p_out = (os.path.abspath(opts["out"]) if "out" in opts
             else default_out(results, set_name, tag_raw))
    # a COMPOSED virtual target's product carries the _comp stem
    # (compose.py writes stack_<target>_comp.fit): when the plain stem is
    # absent and the composed one is solved, default to it — output too,
    # so the product family stays stack_<target>_comp_{wcs,spcc}.fit
    if ("in" not in opts and not os.path.exists(p_in)
            and os.path.exists(os.path.join(
                results, f"stack_{set_name}_comp_wcs.fit"))):
        p_in = os.path.join(results, f"stack_{set_name}_comp_wcs.fit")
        if "out" not in opts:
            p_out = default_out(results, set_name, tag_raw, composed=True)
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

    tag = f"_{tag_raw}" if tag_raw else ""
    spcc_args = f"-catalog={catalog}" + spcc_extra_args(spec)
    rel_in = os.path.relpath(p_in, sdir)
    rel_out = os.path.relpath(p_out, sdir)
    ssf = os.path.join(work, f"spcc_{set_name}{tag}.gen.ssf")
    with open(ssf, "w") as f:
        # setcompress is a PERSISTED siril preference (config.ini), not
        # per-script state — pin it off or the save inherits whatever the
        # last session left and writes .fit.fz where the record expects .fit
        # set32bits for the same reason and with the same force: bit depth is a
        # PERSISTED preference too, and this `save` writes stack_<set>_spcc.fit —
        # the linear product the render tier consumes. Unpinned it inherited
        # whatever ran last, so a 16-bit preference would have quietly written the
        # deliverable's own input at 16 bits (measured cost of integer
        # round-tripping on this chain: 30-45% of the faint extended contrast —
        # docs/dead-ends.md). Enforced by scripts/stack/check_bitdepth.sh.
        # `spcc_list oscsensor` BEFORE `spcc`: the preload that makes the names
        # resolve (docstring; H0) — the log-order assertion below checks it ran.
        f.write("requires 1.4.0\n"
                "setcompress 0\n"
                "setext fit\n"
                "set32bits\n"
                f"load {rel_in[:-4] if rel_in.endswith('.fit') else rel_in}\n"
                "spcc_list oscsensor\n"
                f"spcc {spcc_args}\n"
                f"save {rel_out[:-4] if rel_out.endswith('.fit') else rel_out}\n"
                "close\n")
    print(f"[spcc_run] {rel_in} -> {rel_out} (catalog {catalog})")
    print("[spcc_run] sensor spec: " + " ".join(
        f"{k}='{spec[k]}' ({spec_prov[k]})" for k in SPEC_KEYS if k in spec))
    r = siril_run(["-d", sdir, "-s", ssf],
                       capture_output=True, text=True)
    log = r.stdout + ("\n--- stderr ---\n" + r.stderr if r.stderr else "")
    p_log = os.path.join(work, f"spcc_{set_name}{tag}.log")
    with open(p_log, "w") as f:
        f.write(log)
    if r.returncode != 0 or not os.path.exists(p_out):
        sys.exit(f"spcc_run: siril failed (log: {p_log})\n" + log[-1500:])
    # POST-RUN ASSERTIONS on Siril's own log (docstring): metadata loaded before
    # the names resolved, the model listed by spcc_list, the model echoed by
    # spcc. A failure exits non-zero and writes NO record — a record must never
    # claim a match the log does not show.
    res_ok, resolution = check_log_resolution(log, spec["oscsensor"])
    if not res_ok:
        removed = discard_unverified(p_out)
        sys.exit("spcc_run: RESOLUTION NOT VERIFIED — no record written, product "
                 f"{'removed' if removed else 'absent'} ({rel_out}); log kept at {p_log}: "
                 + "; ".join(resolution["problems"]) + ". " + MECHANISM)

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
    named = {k: spec[k] for k in SPEC_KEYS if k in spec}
    # SENSOR MATCH STATUS rides with every product: what was passed, where each
    # value came from (cli / recipe / default-explicit), and the three log
    # facts that prove Siril resolved THAT model (the assertions above).
    rec = {"set": set_name, "catalog": catalog,
           "sensor_spec": named,
           "sensor_spec_source": spec_prov,
           "sensor_match": (f"named: {spec['oscsensor']} — verified: listed by "
                            "spcc_list, metadata loaded before resolution, echoed "
                            "by spcc"),
           "resolution_check": {k: resolution[k] for k in ("loaded_line", "listed_line", "use_line")},
           "sensor_match_note": ("Resolution is verified per run because " + MECHANISM +
                                 "; the preload + assertions retire when Siril loads "
                                 "before resolving (REMOVAL CONDITION in the docstring)."),
           "sensor_is_dslr": bool(model_info and model_info.get("is_dslr")),
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
    print(f"[spcc_run] SENSOR: {rec['sensor_match']} (lines "
          f"{resolution['loaded_line']}/{resolution['listed_line']}/{resolution['use_line']})")


if __name__ == "__main__":
    sys.exit(main())
