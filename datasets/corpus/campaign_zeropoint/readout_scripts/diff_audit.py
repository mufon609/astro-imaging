#!/usr/bin/env python3
"""GO #9 diff audit: every entry of `git status --short`, classed: equivalent (readiness: only the live df
figure; lens_preflight: identical or a pure superset), new-measurement (solve/spcc records, incl. the new
night/corpus files), scratch-describes-new-product (baseline_corners/edge), not-the-campaign (the
director's working files: BACKLOG.md, docs/), record-dir (campaign_zeropoint/), or FINDING (anything else /
any unexpected content change). Numstat pasted as measured."""
import json, subprocess, os, re
R = "/home/samsung/Desktop/astro-imaging"; W = f"{R}/datasets/corpus/campaign_zeropoint/readout_work"
st = subprocess.run(["git", "-C", R, "status", "--short"], capture_output=True, text=True).stdout.splitlines()
numstat = subprocess.run(["git", "-C", R, "diff", "--numstat"], capture_output=True, text=True).stdout
ns = {l.split("\t")[2]: (l.split("\t")[0], l.split("\t")[1]) for l in numstat.splitlines()}
def old_json(p):
    r = subprocess.run(["git", "-C", R, "show", f"HEAD:{p}"], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None
def diff_keys(o, n, prefix=""):
    ch = []
    if isinstance(o, dict) and isinstance(n, dict):
        for k in set(o) | set(n):
            if k not in o: ch.append(("added", prefix + k))
            elif k not in n: ch.append(("removed", prefix + k))
            else: ch += diff_keys(o[k], n[k], prefix + k + ".")
    elif isinstance(o, list) and isinstance(n, list) and len(o) == len(n):
        for i, (a, b) in enumerate(zip(o, n)): ch += diff_keys(a, b, prefix + f"[{i}].")
    elif o != n: ch.append(("changed", prefix.rstrip(".")))
    return ch
rows = []
for l in st:
    code, path = l[:2].strip(), l[3:]
    row = {"status": code, "path": path, "numstat": ns.get(path)}
    base = os.path.basename(path)
    if code == "??":
        if path.startswith("datasets/corpus/campaign_zeropoint"): row["class"] = "record-dir (this engagement's records + gitignored readout scratch)"
        elif path.startswith("docs/"): row["class"] = "not-the-campaign (director's working file)"
        elif re.match(r"(solve_stack|spcc)_", base): row["class"] = "new-measurement (new file: night/corpus record under REGREF's set)"
        else: row["class"] = "FINDING (unexpected untracked)"
    elif path in ("BACKLOG.md",) or path.startswith("docs/"):
        row["class"] = "not-the-campaign (director's working file)"
    else:
        o, n = old_json(path), (json.load(open(f"{R}/{path}")) if path.endswith(".json") else None)
        ch = diff_keys(o, n) if (o is not None and n is not None) else [("nonjson", path)]
        row["changed"] = sorted(set(c[1] for c in ch))[:12]; row["n_changed"] = len(ch)
        if base == "readiness.json":
            only_disk = all(re.match(r"criteria\.\[\d+\]\.value", c[1]) and (o["criteria"][int(re.search(r"\[(\d+)\]", c[1]).group(1))]["criterion"] == "disk") for c in ch)
            row["class"] = "equivalent (only the live df figure in the disk criterion)" if only_disk else "re-evaluated (readiness rows beyond disk changed — see values)"
            if not only_disk: row["values"] = [(c[1], str(eval("o" + "".join(f"[{int(k[1:-1])}]" if k.startswith("[") else f"[{k!r}]" for k in re.findall(r"\[\d+\]|[A-Za-z_]+", c[1]))))[:110], str(eval("n" + "".join(f"[{int(k[1:-1])}]" if k.startswith("[") else f"[{k!r}]" for k in re.findall(r"\[\d+\]|[A-Za-z_]+", c[1]))))[:110]) for c in ch]
        elif base == "lens_preflight.json":
            adds = [c for c in ch if c[0] == "added"]; others = [c for c in ch if c[0] != "added"]
            row["class"] = "equivalent+superset (keys added, none changed)" if adds and not others else ("equivalent (identical)" if not ch else "FINDING (lens_preflight values changed)")
        elif re.match(r"(solve_stack|spcc)_", base): row["class"] = "new-measurement (the campaign product's solve/SPCC record)"
        elif base in ("baseline_corners.json", "baseline_edge.json"): row["class"] = "scratch-describes-new-product (guard scratch; D4: lands with the re-seeds or is checked out)"
        else: row["class"] = "FINDING (unexpected tracked file changed)"
    rows.append(row)
from collections import Counter
json.dump({"numstat_measured": numstat, "status_short": st, "rows": rows, "classes": Counter(r["class"].split(" (")[0] for r in rows)}, open(f"{W}/diff_audit.json", "w"), indent=1)
print("MEASURED git diff --numstat:\n" + numstat)
print("classes:", Counter(r["class"] for r in rows))
for r in rows:
    if r["class"].startswith("FINDING") or r["class"].startswith("not-the") or "lens_preflight" in r["path"] or "readiness" in r["path"]: print(f"  {r['status']:2} {r['path']:70} {r['class']}  {r.get('changed', '')}")
