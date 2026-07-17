#!/usr/bin/env bash
# Install this repo's darktable lens styles into a darktable config dir.
#
# darktable stores styles in its own sqlite `data.db`; it has no headless import
# for a .dtstyle file (the GUI's styles module is the only interactive route).
# This installs them headlessly so a render is reproducible without a GUI step.
#
# The styles carry ONE effective bit: the lens module's enabled state
# (lensdist=1, nodist=0). darktable IGNORES a style's lens op_params entirely —
# modify_flags included — and re-detects the lens per image, applying its
# DEFAULT correction set (measured: flag/method/lens-string changes in the blob
# produce byte-identical output; docs/dead-ends.md). Distortion-only is
# therefore enforced in the lensfun user DB instead: install_lens_model.sh
# strips this lens's <vignetting>/<tca> calibrations (vignetting correction
# here would double-correct flat-corrected lights). The blob stays pinned so
# the pair is reproducible byte-for-byte, but do not encode intent in it.
#
# Usage: install_styles.sh <configdir>
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CFG=${1:?usage: install_styles.sh <darktable configdir>}
mkdir -p "$CFG"

# darktable creates/migrates data.db on first run; never write that schema by hand.
# Only a real export job triggers it — --version/--help do not — so bootstrap with
# a 1x1 PNG.
if [ ! -f "$CFG/data.db" ]; then
  TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
  base64 -d > "$TMP/seed.png" <<'PNG'
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==
PNG
  darktable-cli "$TMP/seed.png" "$TMP/seed.jpg" --core --configdir "$CFG" \
    --library ":memory:" >/dev/null 2>&1 || true
fi
[ -f "$CFG/data.db" ] || { echo "install_styles: darktable did not create $CFG/data.db" >&2; exit 1; }

python3 - "$CFG/data.db" "$HERE"/*.dtstyle <<'PY'
import sys, sqlite3, xml.etree.ElementTree as ET

db, paths = sys.argv[1], sys.argv[2:]
c = sqlite3.connect(db)
for p in paths:
    r = ET.parse(p).getroot()
    name = r.findtext("info/name")
    desc = r.findtext("info/description") or ""
    c.execute("DELETE FROM style_items WHERE styleid IN (SELECT id FROM styles WHERE name=?)", (name,))
    c.execute("DELETE FROM styles WHERE name=?", (name,))
    cur = c.execute("INSERT INTO styles (name,description,iop_list) VALUES (?,?,?)",
                    (name, desc, r.findtext("info/iop_list")))
    sid = cur.lastrowid
    n = 0
    for pl in r.findall("style/plugin"):
        c.execute(
            "INSERT INTO style_items (styleid,num,module,operation,op_params,enabled,"
            "blendop_params,blendop_version,multi_priority,multi_name,multi_name_hand_edited) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (sid, int(pl.findtext("num")), int(pl.findtext("module")),
             pl.findtext("operation"), bytes.fromhex(pl.findtext("op_params")),
             int(pl.findtext("enabled")),
             bytes.fromhex(pl.findtext("blendop_params") or ""),
             int(pl.findtext("blendop_version")), int(pl.findtext("multi_priority")),
             pl.findtext("multi_name") or "", int(pl.findtext("multi_name_hand_edited") or 0)))
        n += 1
    print(f"installed style {name!r} ({n} module(s)) into {db}")
c.commit()
PY
