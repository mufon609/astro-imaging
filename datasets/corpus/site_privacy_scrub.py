#!/usr/bin/env python3
"""One-off SCRUB for the site-privacy process (owner-directed; docs/dead-ends/evidence-provenance.md,
"THE OBSERVING SITE IS A HOME ADDRESS") — kept beside its record,
datasets/corpus/site_privacy_process.json.

    python3 datasets/corpus/site_privacy_scrub.py [--dry]

For every tracked datasets/<session>/<set>/acquisition.json whose `site` block
carries the coordinates (the 20 that did), rewrite that block through the NEW
scripts/lib/acquisition.site_facts() — provenance only: which gitignored config
resolved, its sha256, status, verified, siteelev_recorded; NO coordinate — and
refresh `_note` to the current constant (the old note pointed at the retired
scripts/setup/site.json). Every OTHER key (`mount`, `mount_source`, `exif`) is
asserted BYTE-IDENTICAL per file: the serializer identity is checked first
(json.dumps(indent=1) reproduces the file's bytes exactly, so equality of the
parsed values IS byte identity of the untouched keys), the raws are not re-read
and nothing is re-derived. A record whose `site` block is already coordinate-free
(july26's lunar sets carry the null block, resolved when no site file existed) is
left untouched and reported. Idempotent. Prints a JSON summary for the record.
"""
import argparse
import glob
import hashlib
import json
import os
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts", "lib"))
import acquisition   # noqa: E402

NUMERIC_SITE_KEYS = ("SITELAT", "SITELONG", "SITEELEV", "OBSGEO_XYZ_m")


def main(dry):
    summary = {"rewritten": [], "untouched": [], "note_refresh": None}
    for path in sorted(glob.glob(os.path.join(REPO, "datasets", "*", "set-*", "acquisition.json"))):
        rel = os.path.relpath(path, REPO)
        old_text = open(path, encoding="utf-8").read()
        old = json.loads(old_text)
        site = old.get("site") or {}
        if not isinstance(site.get("SITELAT"), (int, float)):
            summary["untouched"].append({"file": rel, "why": "site block carries no coordinate",
                                         "resolved_from": site.get("resolved_from")})
            continue
        assert json.dumps(old, indent=1) == old_text, "%s: not in json.dumps(indent=1) form" % rel
        session = rel.split(os.sep)[1]
        new_site = acquisition.site_facts(os.path.join(REPO, "sessions", session))
        assert new_site.get("config_sha256"), "%s: no site config resolved — refusing to write a null block over a real one" % rel
        assert not any(isinstance(new_site.get(k), (int, float)) for k in NUMERIC_SITE_KEYS), "new block carries a number"
        assert "OBSGEO_XYZ_m" not in new_site and "SITELAT" not in new_site
        new = dict(old)
        new["site"] = new_site
        new["_note"] = acquisition._NOTE
        for k in old:
            if k in ("site", "_note"):
                continue
            assert json.dumps(old[k], indent=1) == json.dumps(new[k], indent=1), "%s: key %s changed" % (rel, k)
        new_text = json.dumps(new, indent=1)
        entry = {"file": rel,
                 "keys_asserted_byte_identical": [k for k in old if k not in ("site", "_note")],
                 "old_site_keys_removed": sorted(set(site) - set(new_site)),
                 "new_site_keys": list(new_site),
                 "config_sha256": new_site["config_sha256"],
                 "resolved_from": new_site["resolved_from"],
                 "bytes_before": len(old_text.encode()), "bytes_after": len(new_text.encode()),
                 "sha256_before": hashlib.sha256(old_text.encode()).hexdigest()[:16],
                 "sha256_after": hashlib.sha256(new_text.encode()).hexdigest()[:16]}
        if summary["note_refresh"] is None:
            summary["note_refresh"] = {"old": old.get("_note"), "new": acquisition._NOTE}
        if not dry:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new_text)
            assert json.loads(open(path, encoding="utf-8").read()) == new
        summary["rewritten"].append(entry)
    summary["n_rewritten"] = len(summary["rewritten"])
    summary["n_untouched"] = len(summary["untouched"])
    summary["dry"] = dry
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry", action="store_true", help="report, write nothing")
    sys.exit(main(ap.parse_args().dry))
