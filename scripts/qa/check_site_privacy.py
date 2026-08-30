#!/usr/bin/env python3
"""GUARD — the observing site (a home address) never reaches a tracked file.

    python3 scripts/qa/check_site_privacy.py             the guard (in run_guards)
    python3 scripts/qa/check_site_privacy.py --selftest  positive controls in a scratch repo

WHY THIS EXISTS. The site is load-bearing science (hour angle, altitude, azimuth,
parallactic angle all derive from it) and it is a home address at 11 cm precision;
this tree is meant to be published. It had reached 23 tracked files — 20
acquisition.json `site` blocks, a corpus record, the tracked site file and the
verifier's own record — plus a near-literal in a code comment, and it REGENERATES:
the chain used to write the coordinates into every record on every run. The
owner-directed process (BACKLOG:`site-privacy-vs-public-repo`): the numbers live in
a GITIGNORED config (scripts/setup/site.local.json, or sessions/<session>/site.local.json;
template scripts/setup/site.example.json), read through scripts/lib/acquisition.py
(the one loader); the tracked `site` block carries the config's sha256 and
provenance only; consumers that write horizon-frame quantities round them so the
site cannot be inverted from a record. This guard is what makes that a process
rather than a promise: it goes RED on any form of the value anywhere tracked.

WHAT IT CHECKS, in two independent halves:

  LITERAL SCAN (needs the local config; without one it prints SKIPPED, stated
  not silent). Every form derived from the config is searched in EVERY tracked
  path, in BOTH the working tree and the INDEX (the staged blob of every tracked
  path, so a leak that is staged but deleted from the worktree, or the old
  tracked site file, is still caught): the decimal latitude / longitude (the
  config's own repr, 6 decimals, with and without sign), the sexagesimal strings
  (the config's own plus derived d/m/s variants at 2 and 1 decimals of arc-
  second, in the d° ' " and colon spellings), the three OBSGEO components
  (derived here from lat/lon/elev exactly as acquisition._obsgeo does: full repr,
  to the centimetre, decimetre and METRE, signed and unsigned), and NEAR-LITERAL
  prefixes at 5 and 4 decimals (a transcription error one digit away is still the
  site). Prefix forms are matched with a non-digit lookbehind and are NOT applied
  to tool-emitted numeric tables (*.lst, *.seq) — MEASURED: a 5-decimal prefix
  collides by chance in a Siril star list (datasets/aug06/corner_work/ca_work/
  p_00003.lst) — the exclusion is printed, and the exact forms still scan those
  files. A hit is reported as file:line and the NAME of the form, never the value.
  Also RED: any tracked path named site.local.json, and the former tracked
  scripts/setup/site.json.

  STRUCTURAL CHECK (config-independent, so it runs on a fresh clone and on a rig
  with no config): every tracked JSON file is walked, and any key named SITELAT /
  SITELONG / SITEELEV / OBSGEO_XYZ_m / OBSGEO-X|Y|Z / OBSGEO_X|Y|Z / sitelat_deg /
  sitelong_deg / siteelev_m holding a NUMBER (or a list of numbers), or a
  sitelat_sexagesimal / sitelong_sexagesimal holding a non-null string, is RED —
  that is the shape the leak had, whatever the value.

LIMITS, stated. It cannot see a value written in a form it does not derive (a
different rounding of the sexagesimal seconds, a UTM or MGRS grid reference, a
what3words string) — add the form here when one is found. It scans TRACKED
content and the index, not history: the 429 unpushed commits that carry the
literal are the owner's separate decision (a history rewrite), and this guard
running RED on HEAD's ancestors would be permanent noise, so it does not look
there. A near-literal prefix inside a *.lst/*.seq is not seen (by the exclusion
above). It reads the config through acquisition.load_site_config() and never
prints a coordinate.

REMOVAL CONDITION: the site no longer exists as a local number anywhere the chain
reads — the field-rotation DERIVATION (verify_site.py names it) recovers latitude
and LST from per-frame solves and the config is retired — or the repo stops being
intended for publication and the owner tracks the site deliberately. Until either,
this runs in run_guards (guard + selftest) and the pre-push hook.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "lib"))
import acquisition   # noqa: E402  — the one loader of the local config (and _obsgeo)

NUMERIC_KEYS = {"SITELAT", "SITELONG", "SITEELEV", "OBSGEO_XYZ_m",
                "OBSGEO-X", "OBSGEO-Y", "OBSGEO-Z", "OBSGEO_X", "OBSGEO_Y", "OBSGEO_Z",
                "sitelat_deg", "sitelong_deg", "siteelev_m"}
STRING_KEYS = {"sitelat_sexagesimal", "sitelong_sexagesimal"}
PREFIX_EXCLUDED_SUFFIXES = (".lst", ".seq")      # tool-emitted numeric tables (measured collision)
FORBIDDEN_TRACKED_BASENAMES = ("site.local.json",)
FORMER_TRACKED_SITE = "scripts/setup/site.json"


# ----------------------------------------------------------------- forms ----
def _sexagesimal_variants(deg_value, pos, neg):
    """d/m/s spellings of one coordinate: the d°'" forms and the colon form, at
    2 and 1 decimals of arcsecond, with the hemisphere letter and without it."""
    a = abs(deg_value)
    d = int(a)
    m = int((a - d) * 60)
    s = (a - d - m / 60.0) * 3600.0
    hemi = pos if deg_value >= 0 else neg
    out = []
    for sec in ("%.2f" % s, "%.1f" % s):
        core_d = "%dd%02d'%s\"" % (d, m, sec)
        core_deg = "%d°%02d'%s\"" % (d, m, sec)
        core_col = "%d:%02d:%s" % (d, m, sec)
        out += [core_d + hemi, core_d, core_deg + hemi, core_deg, core_col]
    return out


def forms_from_config(cfg):
    """Every searchable form of the site in the config: [(name, kind, text)],
    kind 'exact' (substring) or 'prefix' (non-digit lookbehind regex)."""
    lat, lon = float(cfg["sitelat_deg"]), float(cfg["sitelong_deg"])
    elev = cfg.get("siteelev_m")
    forms = []

    def add_num(name, v):
        seen = set()
        for txt in (repr(v), "%.6f" % v):
            for t in (txt, txt.lstrip("-")):
                if t not in seen and len(t) >= 6:
                    seen.add(t)
                    forms.append((name, "exact", t))
        s = repr(abs(v))
        if "." in s:
            ip, fp = s.split(".", 1)
            for nd in (5, 4):
                if len(fp) > nd:
                    forms.append(("%s_prefix%d" % (name, nd), "prefix", "%s.%s" % (ip, fp[:nd])))

    add_num("lat_decimal", lat)
    add_num("lon_decimal", lon)
    for key, name in (("sitelat_sexagesimal", "lat_sexagesimal_config"),
                      ("sitelong_sexagesimal", "lon_sexagesimal_config")):
        v = cfg.get(key)
        if isinstance(v, str) and v.strip():
            forms.append((name, "exact", v.strip()))
    for v in _sexagesimal_variants(lat, "N", "S"):
        forms.append(("lat_sexagesimal_derived", "exact", v))
    for v in _sexagesimal_variants(lon, "E", "W"):
        forms.append(("lon_sexagesimal_derived", "exact", v))
    xyz = acquisition._obsgeo(lat, lon, elev)
    for comp, v in zip("XYZ", xyz):
        seen = set()
        for txt in (repr(v), "%.2f" % v, "%.1f" % v, "%.0f" % v):
            for t in (txt, txt.lstrip("-")):
                if t not in seen and len(t) >= 6:
                    seen.add(t)
                    forms.append(("obsgeo_%s" % comp, "exact", t))
    # JSON-ESCAPED twins: inside a .json string a `"` is `\"` and a `°` is
    # `°`, so the sexagesimal forms hide from a plain search — MEASURED: the
    # tracked site file carried them and `git grep -F` on the plain form found 0.
    for name, kind, text in list(forms):
        if kind == "exact":
            esc = json.dumps(text)[1:-1]
            if esc != text:
                forms.append((name + "_jsonescaped", "exact", esc))
    # dedupe on (kind, text), keep the first name
    out, seen = [], set()
    for name, kind, text in forms:
        if (kind, text) not in seen:
            seen.add((kind, text))
            out.append((name, kind, text))
    return out


def _compile(forms):
    """Every form as a regex with a non-digit / non-dot LOOKBEHIND, so the site's
    decimal cannot be matched inside a longer unrelated number (MEASURED in the
    selftest: a planted 12.345678 matched inside 'RA 312.345678'). No lookahead:
    a longer decimal that BEGINS with the site's digits is the site at more
    precision, and the prefix forms need exactly that."""
    return [(name, kind, re.compile(r"(?<![\d.])" + re.escape(text))) for name, kind, text in forms]


# --------------------------------------------------------------- sources ----
def _git(root, *args):
    return subprocess.run(["git", "-C", root] + list(args), capture_output=True,
                          text=True, check=True).stdout


def tracked_paths(root):
    return [p for p in _git(root, "ls-files", "-z").split("\0") if p]


def index_blobs(root):
    """{path: bytes} of every tracked path's INDEX blob, in one cat-file batch."""
    rows = [r for r in _git(root, "ls-files", "-s", "-z").split("\0") if r]
    shas, paths = [], []
    for r in rows:
        meta, path = r.split("\t", 1)
        mode, sha, _stage = meta.split()
        if mode == "120000":       # a symlink: its blob is the target path, not content
            continue
        shas.append(sha)
        paths.append(path)
    if not shas:
        return {}
    p = subprocess.run(["git", "-C", root, "cat-file", "--batch"],
                       input=("\n".join(shas) + "\n").encode(), capture_output=True, check=True)
    out, buf, i = {}, p.stdout, 0
    for sha, path in zip(shas, paths):
        nl = buf.index(b"\n", i)
        header = buf[i:nl].decode()
        i = nl + 1
        parts = header.split()
        if len(parts) != 3:          # "<sha> missing"
            continue
        size = int(parts[2])
        out[path] = buf[i:i + size]
        i += size + 1                # the trailing newline
    return out


def _text(b):
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return None


# ---------------------------------------------------------------- checks ----
def scan_literals(root, cfg):
    """[(path, line, source, form_name)] over worktree + index. `cfg` None -> None."""
    if cfg is None:
        return None
    compiled = _compile(forms_from_config(cfg))
    exact = [(n, rx) for n, k, rx in compiled if k == "exact"]
    prefix = [(n, rx) for n, k, rx in compiled if k == "prefix"]
    hits = []
    blobs = index_blobs(root)
    for path in tracked_paths(root):
        sources = []
        wt = os.path.join(root, path)
        if os.path.isfile(wt) and not os.path.islink(wt):
            with open(wt, "rb") as fh:
                sources.append(("worktree", fh.read()))
        if path in blobs:
            sources.append(("index", blobs[path]))
        prefix_ok = not path.endswith(PREFIX_EXCLUDED_SUFFIXES)
        for src, data in sources:
            txt = _text(data)
            if txt is None:
                continue
            quick = any(rx.search(txt) for _, rx in exact) or (
                prefix_ok and any(rx.search(txt) for _, rx in prefix))
            if not quick:
                continue
            for ln, line in enumerate(txt.split("\n"), 1):
                for name, rx in exact:
                    if rx.search(line):
                        hits.append((path, ln, src, name))
                if prefix_ok:
                    for name, rx in prefix:
                        if rx.search(line):
                            hits.append((path, ln, src, name))
    return sorted(set(hits))


def scan_tracked_names(root):
    bad = []
    for path in tracked_paths(root):
        if os.path.basename(path) in FORBIDDEN_TRACKED_BASENAMES:
            bad.append((path, "a site.local.json is TRACKED — it must be gitignored"))
        if path == FORMER_TRACKED_SITE:
            bad.append((path, "the former tracked site file is still in the index — "
                              "`git rm --cached %s` (the config is site.local.json)" % path))
    return bad


def _walk(obj, path, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = path + "/" + str(k)
            if k in NUMERIC_KEYS:
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    out.append((here, "number"))
                elif isinstance(v, list) and v and all(
                        isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
                    out.append((here, "list of numbers"))
            if k in STRING_KEYS and isinstance(v, str) and v.strip():
                out.append((here, "non-null string"))
            _walk(v, here, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _walk(v, path + "[%d]" % i, out)


def scan_structural(root):
    """[(path, json_path, what)] over every tracked *.json (worktree + index)."""
    hits, n = [], 0
    blobs = index_blobs(root)
    for path in tracked_paths(root):
        if not path.endswith(".json"):
            continue
        n += 1
        sources = []
        wt = os.path.join(root, path)
        if os.path.isfile(wt):
            with open(wt, "rb") as fh:
                sources.append(("worktree", fh.read()))
        if path in blobs:
            sources.append(("index", blobs[path]))
        for src, data in sources:
            try:
                obj = json.loads(data.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                continue
            found = []
            _walk(obj, "", found)
            for jp, what in found:
                hits.append((path, jp, "%s (%s)" % (what, src)))
    return sorted(set(hits)), n


def report(root, cfg, cfg_where):
    names = scan_tracked_names(root)
    lit = scan_literals(root, cfg)
    struct, n_json = scan_structural(root)
    n_paths = len(tracked_paths(root))
    red = bool(names or lit or struct)
    print("=== check_site_privacy under %s ===" % root)
    if cfg is None:
        print("  literal scan: SKIPPED — no local site config (%s); the structural "
              "check below still ran" % cfg_where)
    else:
        n_wt = sum(1 for h in lit if h[2] == "worktree")
        n_ix = sum(1 for h in lit if h[2] == "index")
        print("  literal scan: %d forms from the config (%s), %d tracked paths, "
              "worktree + index; prefix forms not applied to %s — %d hit(s): "
              "%d in the worktree, %d in the index%s"
              % (len(forms_from_config(cfg)), cfg_where, n_paths,
                 "/".join("*" + s for s in PREFIX_EXCLUDED_SUFFIXES), len(lit), n_wt, n_ix,
                 " (an index-only hit is a STAGED blob — a scrubbed file whose "
                 "old content is still in the index until `git add -u`, or a "
                 "deleted file until its removal is staged)" if n_ix and not n_wt else ""))
        for path, ln, src, name in lit:
            print("    RED  %s:%d  [%s]  %s" % (path, ln, src, name))
    print("  structural check: %d tracked JSON files (worktree + index) — %d hit(s)"
          % (n_json, len(struct)))
    for path, jp, what in struct:
        print("    RED  %s  %s  %s" % (path, jp, what))
    for path, why in names:
        print("    RED  %s  %s" % (path, why))
    if red:
        print("RED: the observing site (or its shape) is in tracked content — see the "
              "lines above. Nothing was rewritten.")
        return 1
    print("OK: site privacy — no form of the site in %d tracked paths (worktree + "
          "index); structural check clean over %d JSON files; literal scan %s."
          % (n_paths, n_json, "ran" if cfg is not None else "SKIPPED (no config)"))
    return 0


# --------------------------------------------------------------- selftest ---
def selftest():
    """Positive controls in a scratch git repo with a PLANTED site (fictitious
    coordinates). Each planted form MUST go RED, the clean tree MUST pass, the
    stated *.lst exclusion MUST hold, and an index-only leak MUST be caught."""
    fail = 0

    def check(label, ok, detail=""):
        nonlocal fail
        print("  %s  %s%s" % ("PASS" if ok else "*** FAIL ***", label,
                             ("  " + detail) if detail else ""))
        if not ok:
            fail += 1

    cfg = {"sitelat_deg": 12.345678, "sitelong_deg": -98.765432, "siteelev_m": None,
           "sitelat_sexagesimal": "12d20'44.44\"N", "sitelong_sexagesimal": "98d45'55.56\"W"}
    xyz = acquisition._obsgeo(cfg["sitelat_deg"], cfg["sitelong_deg"], None)
    base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    os.makedirs(base, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="check_site_privacy.", dir=base) as d:
        subprocess.run(["git", "init", "-q", d], check=True)

        def plant(name, text, stage=True):
            p = os.path.join(d, name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as fh:
                fh.write(text)
            if stage:
                subprocess.run(["git", "-C", d, "add", "--", name], check=True)
            return p

        def unplant(name):
            subprocess.run(["git", "-C", d, "rm", "-q", "--cached", "--", name], check=True)
            os.remove(os.path.join(d, name))

        # clean tree: a null site block + unrelated numbers that share digits
        plant("datasets/x/acquisition.json", json.dumps(
            {"site": {"SITELAT": None, "SITELONG": None, "resolved_from": None},
             "exif": {"focal_mm": 12.3, "iso": 98765}}, indent=1))
        plant("notes.md", "FWHM 2.3457 px; a scale of 17.5031 arcsec/px; RA 312.345678 deg "
                          "(the site's digits inside a LONGER number — must not match)\n")
        names, lit, (struct, _) = (scan_tracked_names(d), scan_literals(d, cfg), scan_structural(d))
        check("clean tree passes (null site block, look-alike numbers)",
              not names and not lit and not struct, "%r %r %r" % (names, lit, struct))

        # the planted forms — each MUST go RED, and the form must be NAMED
        arms = [
            ("planted decimal latitude in a .md", "leak_dec.md", "site lat %r\n" % cfg["sitelat_deg"], "lat_decimal"),
            ("planted sexagesimal INSIDE a JSON string (escaped quote)", "leak_sexa_esc.json",
             json.dumps({"where": cfg["sitelat_sexagesimal"]}), "lat_sexagesimal_config_jsonescaped"),
            ("planted degree-sign sexagesimal, JSON-escaped (\\u00b0)", "leak_deg_esc.json",
             json.dumps({"where": "12°20'44.44\"N"}), "lat_sexagesimal_derived_jsonescaped"),
            ("planted 6-decimal longitude, unsigned", "leak_lon.txt", "lon %.6f\n" % abs(cfg["sitelong_deg"]), "lon_decimal"),
            ("planted sexagesimal string in a .txt (plain)", "leak_sexa.txt",
             "at " + cfg["sitelat_sexagesimal"] + "\n", "lat_sexagesimal_config"),
            ("planted derived sexagesimal (colon form)", "leak_colon.txt", "12:20:44.4\n", "lat_sexagesimal_derived"),
            ("planted OBSGEO component to the metre", "leak_obsgeo.txt", "X %.0f m\n" % xyz[0], "obsgeo_X"),
            ("planted OBSGEO component, full repr, negative", "leak_obsgeo2.txt", "Y=%r\n" % xyz[1], "obsgeo_Y"),
            ("planted NEAR-literal (5-decimal prefix, last digit off)", "leak_near.py",
             "# transposed: 12.345671 -> ...\n", "lat_decimal_prefix5"),
        ]
        for label, name, text, expect in arms:
            plant(name, text)
            lit = scan_literals(d, cfg)
            got = {h[3] for h in lit if h[0] == name}
            check(label + " -> RED, named", expect in got, "forms hit: %s" % sorted(got))
            unplant(name)

        # the stated exclusion: a prefix inside a *.lst is NOT a hit, an exact form still is
        plant("stars.lst", "1\t12.34567\t9.9\n")
        lit = scan_literals(d, cfg)
        check("5-decimal prefix in a *.lst is NOT flagged (stated exclusion)",
              not [h for h in lit if h[0] == "stars.lst"], repr(lit))
        unplant("stars.lst")
        plant("stars2.lst", "1\t%r\t9.9\n" % cfg["sitelat_deg"])
        lit = scan_literals(d, cfg)
        check("the EXACT decimal inside a *.lst IS flagged",
              bool([h for h in lit if h[0] == "stars2.lst"]), repr(lit))
        unplant("stars2.lst")

        # index-only leak: staged, then deleted from the worktree — the index scan must see it
        plant("staged_only.md", "lat %r\n" % cfg["sitelat_deg"])
        os.remove(os.path.join(d, "staged_only.md"))
        lit = scan_literals(d, cfg)
        check("a leak that is STAGED but deleted from the worktree is caught (index scan)",
              any(h[0] == "staged_only.md" and h[2] == "index" for h in lit), repr(lit))
        subprocess.run(["git", "-C", d, "rm", "-q", "--cached", "--", "staged_only.md"], check=True)

        # structural: a numeric site block with NO config at all
        plant("datasets/y/acquisition.json", json.dumps(
            {"site": {"SITELAT": 12.345678, "SITELONG": -98.765432,
                      "OBSGEO_XYZ_m": xyz}}, indent=1))
        struct, _ = scan_structural(d)
        check("numeric `site` block -> structural RED (no config needed)",
              len(struct) >= 3, repr(struct))
        check("literal scan without a config returns SKIPPED, not a pass",
              scan_literals(d, None) is None)
        unplant("datasets/y/acquisition.json")
        plant("cfg_leak.json", json.dumps({"sitelat_deg": 12.3, "sitelong_sexagesimal": "12d20'44\"N"}))
        struct, _ = scan_structural(d)
        check("numeric sitelat_deg / non-null sexagesimal key -> structural RED",
              {what.split(" (")[0] for _, _, what in struct} >= {"number", "non-null string"}, repr(struct))
        unplant("cfg_leak.json")

        # a tracked site.local.json, and the former tracked site file, are RED by name
        plant("scripts/setup/site.local.json", "{}")
        plant("scripts/setup/site.json", "{}")
        names = scan_tracked_names(d)
        check("a TRACKED site.local.json and the former scripts/setup/site.json -> RED by name",
              len(names) == 2, repr(names))
        unplant("scripts/setup/site.local.json")
        unplant("scripts/setup/site.json")

        # the clean tree again, after every arm — nothing leaked from the fixture
        names, lit, (struct, _) = (scan_tracked_names(d), scan_literals(d, cfg), scan_structural(d))
        check("clean tree passes after every arm", not names and not lit and not struct)

    print("SELFTEST %s (%d failure(s))" % ("PASSED" if not fail else "FAILED", fail))
    return 1 if fail else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--root", default=REPO, help="repo to scan (default: this repo)")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    cfg, path, which, _sha = acquisition.load_site_config()
    where = which if cfg is not None else "no scripts/setup/site.local.json"
    sys.exit(report(os.path.normpath(a.root), cfg, where))
