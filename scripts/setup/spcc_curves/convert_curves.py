#!/usr/bin/env python3
"""Convert the two fetched proxy responses into siril-spcc-database OSC_SENSOR
files and (optionally) install them into the machine-local database clone.
BACKLOG:spcc-sensor-curve stage 1; the why is docs/spcc-sensor-curve-z6iii.md
sections 1.4-1.6 (the proxies, the QE-vs-responsivity convention).

  convert_curves.py [--cache=DIR] [--db=DIR] [--out=DIR] [--install] [--summary=FILE]

Inputs (fetch_sources.sh, sha256-pinned): the Weta/ASWF Nikon Z f JSON
(physlight schema 0.1.0: spectral_data.data.main[<nm>] = [R, G, B], units
"relative", 380-780 nm at 5 nm) and Butcher's Nikon Z 6 CSV (wavelength,R,G,B;
400-715 nm at 5 nm; '#' comment lines).

Outputs, three files, three `model` strings exactly as `spcc_list oscsensor`
will print them:
  Nikon_Zf.json         model "Nikon Z f"          photon-based   marker 3  TRACKED (Apache-2.0)
  Nikon_Zf_energy.json  model "Nikon Z f (energy)" as shipped     marker 3  TRACKED (Apache-2.0)
  Nikon_Z6.json         model "Nikon Z6"           photon-based   marker 2  cache only (CC BY-NC-SA 4.0)

The conversion. Siril multiplies each Gaia XP flux sample by its wavelength
(photon counting, src/algos/spcc.c flux_to_relcount) and treats the sensor
curve as QE. A response measured per unit incident POWER is R_E(lambda) =
QE(lambda) * lambda / hc, so the QE-shaped curve is R_E / lambda. "photon-based"
= every channel divided by its wavelength in nm, then all three channels
divided by ONE global maximum (inter-channel scale preserved; max = 1.0,
range 1), rounded to 6 significant digits. "(energy)" = the source values
verbatim, range 1 — the arm that measures how much the convention moves K.
Neither source states which convention its "relative" values carry
(RECORD.json, premises_untested); the (energy) twin exists for that reason.

The JSON objects are produced by the database's OWN generator
(utils/process_osc_sensor.py: a 6-column WebPlotDigitizer CSV x_R,y_R,x_G,y_G,
x_B,y_B -> the three-object array, invoked exactly as recorded in the summary),
then three metadata fields it hard-codes are overwritten: dataQualityMarker
(it writes 2), comment (it writes "Covers all cameras using this chip"), and
the `name` suffixes are kept as it wrote them ("<model> Red/Green/Blue"). No
numeric value is touched after the generator runs.

Validation is the schema's required set checked by hand (no jsonschema on
this rig): root array; type/model/name/manufacturer/dataSource strings;
dataQualityMarker int 1-5; version int >= 1; channel RED/GREEN/BLUE, one each;
wavelength.value numbers >= 0 strictly increasing, units in the enum;
values.value numbers >= 0 (finite), values.range > 0; 5-2000 points; equal
lengths; identical model across the three objects; no is_dslr (a stock body's
hot mirror is inside a whole-camera curve, and an is_dslr model would require
-osclpf= after the runner's preload). Any failure exits non-zero and installs
nothing.

--install copies the three files into <db>/osc_sensors/ as NEW files (refuses
to overwrite a file git tracks there: the GUI's hard reset would revert an
edit and leave a new file; this rig runs auto_update_spcc=false).

REMOVAL CONDITION: retire the Nikon Z f proxy — the recipes' spcc block and
these converted files (Nikon_Zf.json, Nikon_Zf_energy.json, the cache-only
Nikon_Z6.json) — when a curve measured on this body (a grating measurement,
docs/spcc-sensor-curve-z6iii.md section 1.5 B1) or an upstream "Nikon Z6 III"
OSC_SENSOR entry lands; re-check whenever the siril-spcc-database clone is
updated.
"""
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys

DEF_CACHE = os.path.expanduser("~/.cache/astro-imaging/spcc_curves")
DEF_DB = os.path.expanduser("~/.var/app/org.siril.Siril/data/siril-spcc-database")
HERE = os.path.dirname(os.path.abspath(__file__))
UNITS_ENUM = ("nm", "micrometer", "angstrom", "m")
CHANNELS = ("RED", "GREEN", "BLUE")

ZF_SRC = ("https://github.com/AcademySoftwareFoundation/rawtoaces-data/blob/"
          "cf6452c3ce44112f6cf3f1c2d7bf6381a4c90638/data/camera/Nikon_Z_f_380_780_5.json "
          "(Weta Digital physlight camera SSF, 'lightsaber' rig, doi:10.5281/zenodo.6590768; Apache-2.0)")
Z6_SRC = ("https://github.com/butcherg/ssf-data/blob/dce9021f98bc28942a8f84ca3cdb5e791f3a1931/"
          "Nikon/Z6/spectroscope/Nikon_Z6_ssf.csv (Glenn Butcher, DIY transmissive-grating "
          "spectroscope + ssftool, 2020-08-27, lens NIKKOR Z 24-70mm f/4 S; CC BY-NC-SA 4.0)")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sig6(x):
    return float(f"{x:.6g}")


def read_zf(path):
    d = json.load(open(path))
    main = d["spectral_data"]["data"]["main"]
    wl = sorted(int(k) for k in main)
    return wl, [[main[str(w)][i] for w in wl] for i in range(3)], d["header"]


def read_z6(path):
    wl, chans = [], [[], [], []]
    with open(path) as f:
        for row in csv.reader(l for l in f if l.strip() and not l.startswith("#")):
            wl.append(int(float(row[0])))
            for i in range(3):
                chans[i].append(float(row[1 + i]))
    return wl, chans


def photon_convert(wl, chans):
    """R_E / lambda, one global maximum -> 1.0, 6 significant digits."""
    div = [[v / w for v, w in zip(c, wl)] for c in chans]
    gmax = max(max(c) for c in div)
    return [[sig6(v / gmax) for v in c] for c in div]


def write_wpd_csv(path, wl, chans):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        for i, x in enumerate(wl):
            w.writerow([x, chans[0][i], x, chans[1][i], x, chans[2][i]])


def run_generator(db, csv_path, manufacturer, model, source):
    gen = os.path.join(db, "utils", "process_osc_sensor.py")
    argv = [sys.executable, gen, csv_path, "--manufacturer", manufacturer,
            "--model", model, "--dataSource", source]
    r = subprocess.run(argv, capture_output=True, text=True, check=True)
    return json.loads(r.stdout), argv


def validate(objs, model):
    """The schema's required set + the Siril loader's own requirements, by hand."""
    problems = []
    if not isinstance(objs, list) or len(objs) != 3:
        return [f"root must be an array of exactly 3 objects (got {type(objs).__name__} {len(objs) if isinstance(objs, list) else ''})"]
    seen = []
    for o in objs:
        for k in ("model", "name", "manufacturer", "dataSource"):
            if not isinstance(o.get(k), str) or not o[k]:
                problems.append(f"{k} missing/empty")
        if o.get("type") != "OSC_SENSOR":
            problems.append(f"type {o.get('type')!r}")
        if o.get("model") != model:
            problems.append(f"model {o.get('model')!r} != {model!r}")
        q, v = o.get("dataQualityMarker"), o.get("version")
        if not (isinstance(q, int) and 1 <= q <= 5):
            problems.append(f"dataQualityMarker {q!r}")
        if not (isinstance(v, int) and v >= 1):
            problems.append(f"version {v!r}")
        if o.get("channel") not in CHANNELS:
            problems.append(f"channel {o.get('channel')!r}")
        seen.append(o.get("channel"))
        if "is_dslr" in o:
            problems.append("is_dslr present (must be absent for a whole-camera curve)")
        wl, va = o.get("wavelength", {}), o.get("values", {})
        x, y = wl.get("value"), va.get("value")
        if wl.get("units") not in UNITS_ENUM:
            problems.append(f"wavelength.units {wl.get('units')!r}")
        if not (isinstance(va.get("range"), (int, float)) and va["range"] > 0):
            problems.append(f"values.range {va.get('range')!r}")
        if not (isinstance(x, list) and isinstance(y, list)):
            problems.append("wavelength.value / values.value not arrays")
            continue
        if len(x) != len(y):
            problems.append(f"array lengths differ {len(x)} != {len(y)}")
        if not (5 <= len(x) <= 2000):
            problems.append(f"{len(x)} points (5-2000 required)")
        if any((not isinstance(a, (int, float))) or a < 0 for a in x):
            problems.append("wavelength has a non-number or negative")
        if any(b >= a for a, b in zip(x[1:], x[:-1])):
            problems.append("wavelength not strictly increasing")
        if any((not isinstance(a, (int, float))) or a < 0 or not math.isfinite(a) for a in y):
            problems.append("values has a non-number, negative or non-finite")
    if sorted(seen) != sorted(CHANNELS):
        problems.append(f"channels {seen} (need one RED, one GREEN, one BLUE)")
    return problems


def stats(objs):
    out = {}
    for o in objs:
        x, y = o["wavelength"]["value"], o["values"]["value"]
        pk = max(y)
        i655 = x.index(655) if 655 in x else None
        out[o["channel"]] = {"peak": pk, "peak_nm": x[y.index(pk)],
                             "at_655nm_over_peak": (y[i655] / pk) if i655 is not None else None,
                             "n": len(x), "range_nm": [x[0], x[-1]]}
    return out


def build(db, cache, out_dir, install):
    summary = {"generator": os.path.join(db, "utils", "process_osc_sensor.py"),
               "inputs": {}, "outputs": {}, "installed": {}, "validation": {}}
    for name in ("Nikon_Z_f_380_780_5.json", "Nikon_Z6_ssf.csv"):
        p = os.path.join(cache, name)
        summary["inputs"][name] = {"path": p, "sha256": sha256(p)}

    wl_zf, ch_zf, hdr = read_zf(os.path.join(cache, "Nikon_Z_f_380_780_5.json"))
    wl_z6, ch_z6 = read_z6(os.path.join(cache, "Nikon_Z6_ssf.csv"))
    zf_note = (f"Source: {ZF_SRC}; source header: laboratory {hdr.get('laboratory')}, "
               f"equipment {hdr.get('measurement_equipment')}, document {hdr.get('unique_identifier')}, "
               f"units 'relative', 380-780 nm at 5 nm. Whole-camera response (body filters inside), "
               f"no is_dslr, so use with -oscfilter='No filter'. Proxy for the Nikon Z6 III "
               f"(IMX820AQJ; no measured curve exists) — BACKLOG spcc-sensor-curve.")
    jobs = [
        ("Nikon_Zf.json", "Z f", ZF_SRC, wl_zf, photon_convert(wl_zf, ch_zf), 3,
         "PHOTON-BASED: each channel divided by wavelength (nm) then all three by one global "
         "maximum (max 1.0, 6 significant digits) — the source is read as response per unit "
         "POWER and Siril integrates a photon spectrum against a QE curve. " + zf_note,
         os.path.join(out_dir, "Nikon_Zf.json")),
        ("Nikon_Zf_energy.json", "Z f (energy)", ZF_SRC, wl_zf, [list(c) for c in ch_zf], 3,
         "AS SHIPPED (energy-based, no /wavelength): the twin of 'Nikon Z f' that measures how "
         "much the QE-vs-responsivity convention moves SPCC's K and fit. " + zf_note,
         os.path.join(out_dir, "Nikon_Zf_energy.json")),
        ("Nikon_Z6.json", "Z6", Z6_SRC, wl_z6, photon_convert(wl_z6, ch_z6), 2,
         "PHOTON-BASED: each channel divided by wavelength (nm) then all three by one global "
         "maximum (max 1.0, 6 significant digits); source values are two-decimal, 400-715 nm at "
         "5 nm, single-image DIY grating measurement with lamp-power compensation of unstated "
         "provenance (dataQualityMarker 2). Whole-camera + lens response, no is_dslr, use with "
         "-oscfilter='No filter'. Licence CC BY-NC-SA 4.0 (copyright 2020 Glenn Butcher): "
         "machine-local use only, not redistributed. Source: " + Z6_SRC,
         os.path.join(cache, "Nikon_Z6.json")),
    ]
    ok_all = True
    for fname, model_suffix, source, wl, chans, marker, comment, dest in jobs:
        csv_path = os.path.join(cache, fname.replace(".json", ".wpd.csv"))
        write_wpd_csv(csv_path, wl, chans)
        objs, argv = run_generator(db, csv_path, "Nikon", model_suffix, source)
        model = f"Nikon {model_suffix}"
        for o in objs:
            o["dataQualityMarker"] = marker
            o["comment"] = comment
        problems = validate(objs, model)
        summary["validation"][fname] = problems or "PASS"
        summary["outputs"][fname] = {"model": model, "generator_argv": argv, "dest": dest,
                                     "stats": stats(objs) if not problems else None}
        if problems:
            ok_all = False
            print(f"{fname}: INVALID — " + "; ".join(problems), file=sys.stderr)
            continue
        with open(dest, "w") as f:
            json.dump(objs, f, indent=1)
            f.write("\n")
        summary["outputs"][fname]["sha256"] = sha256(dest)
        summary["outputs"][fname]["names"] = [o["name"] for o in objs]
    if not ok_all:
        return summary, 1
    if install:
        tracked = set(subprocess.run(["git", "-C", db, "ls-files", "osc_sensors"],
                                     capture_output=True, text=True).stdout.split())
        for fname, info in summary["outputs"].items():
            rel = f"osc_sensors/{fname}"
            if rel in tracked:
                print(f"REFUSED: {rel} is tracked upstream in the clone — a new file only", file=sys.stderr)
                return summary, 1
            dst = os.path.join(db, rel)
            shutil.copyfile(info["dest"], dst)
            summary["installed"][fname] = {"path": dst, "sha256": sha256(dst)}
    return summary, 0


def main():
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    flags = {a for a in sys.argv[1:] if a.startswith("--") and "=" not in a}
    cache = opts.get("cache", DEF_CACHE)
    db = opts.get("db", DEF_DB)
    out_dir = opts.get("out", HERE)
    summary, rc = build(db, cache, out_dir, "--install" in flags)
    text = json.dumps(summary, indent=1)
    if "summary" in opts:
        with open(opts["summary"], "w") as f:
            f.write(text + "\n")
    print(text)
    sys.exit(rc)


if __name__ == "__main__":
    main()
