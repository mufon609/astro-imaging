#!/usr/bin/env bash
# ONE-TIME backfill of optics/calibration provenance onto sub-stacks built
# BEFORE the stamp existed (stamp_headers.sh `header_provenance_lines`).
#
#   backfill_substack_provenance.sh [--dry-run]
#
# WHY IT EXISTS. The combine contract makes a sub-stack self-describing so a
# night months from now can be composed against it with no external lookup and
# no machine state. Every sub-stack on this rig predates that stamp and carries
# nothing — so without this they are outside the contract, and the compose gate
# would read them all as UNKNOWN forever.
#
# WHY IT IS SAFE TO BACKFILL AT ALL. Each of these members' installed model is
# known EXACTLY, not inferred: `lens_preflight.py` wrote what it read live from
# the lensfun DB at each build, and those records are COMMITTED. The per-set
# record is overwritten by each later build, so the authority for a given member
# dir is the record AT THE COMMIT contemporaneous with that build — cited per row
# below and recoverable with `git show <commit>:<path>`. DISTSRC carries
# `backfill:<commit>` so a reader can tell a stamped-at-build value from a
# reconstructed one and go check.
#
# The calibration side (CALDARK/CALFLAT/CALSET) comes from the tracked
# `skyflat_<set>_qa.json`, which was never overwritten across these builds.
#
# This writes FITS HEADERS ONLY — no pixel is read or altered (the same access
# run_undistort_groups.sh already takes to stamp GRPSIZE).
#
# Removal condition: retires once no un-stamped sub-stack remains on any rig
# this repo is cloned to — i.e. after the archive is rebuilt at least once under
# a chain that stamps at warp time.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

# dir : a : b : c : session/set : provenance-commit
# The models, each traced to the committed lens_preflight.json of that build:
#   aug06 own-model arm    -> 295aa26   (the own-model rebuilds, 08-08 05:45-07:37)
#   aug06 pinned control   -> 4771780 (set-01) / b5f9a36 (set-02,03)
#   aug06 subsky1 arm      -> same per-set own models (driver.sh installs the
#                             set's own record per set before each build)
#   july31 all four sets   -> the july14-fitted state, INHERITED with recorded
#                             provenance (each set's lens_fit.json), preflight ok
#   aug06 set-00           -> its own fit (lens_fit.json, single build)
ROWS=(
"sessions/aug06/work/groups_set-00:0.00493263092699596:0.0125447075852702:0.00297176913257466:aug06/set-00:own"
"sessions/aug06/work/groups_set-01:0.00808615198829015:0.00191793356594816:0.012386006221812:aug06/set-01:own@295aa26"
"sessions/aug06/work/groups_set-02:0.00191581277686593:0.0199376108933101:-0.000710974017555417:aug06/set-02:own@295aa26"
"sessions/aug06/work/groups_set-03:0.00428141725248721:0.0119442691335761:0.00157443438620187:aug06/set-03:own@295aa26"
"sessions/aug06/work/groups_set-01_subsky1:0.00808615198829015:0.00191793356594816:0.012386006221812:aug06/set-01:own@295aa26"
"sessions/aug06/work/groups_set-02_subsky1:0.00191581277686593:0.0199376108933101:-0.000710974017555417:aug06/set-02:own@295aa26"
"sessions/aug06/work/groups_set-03_subsky1:0.00428141725248721:0.0119442691335761:0.00157443438620187:aug06/set-03:own@295aa26"
"sessions/aug06/work/groups_set-01_pinned:0.00350093:0.01453356:0.00043983:aug06/set-01:pinned@4771780"
"sessions/aug06/work/groups_set-02_pinned:0.00350093:0.01453356:0.00043983:aug06/set-02:pinned@b5f9a36"
"sessions/aug06/work/groups_set-03_pinned:0.00350093:0.01453356:0.00043983:aug06/set-03:pinned@b5f9a36"
"sessions/july31/work/groups_set-01:0.00350093:0.01453356:0.00043983:july31/set-01:inherited-july14"
"sessions/july31/work/groups_set-02:0.00350093:0.01453356:0.00043983:july31/set-02:inherited-july14"
"sessions/july31/work/groups_set-03:0.00350093:0.01453356:0.00043983:july31/set-03:inherited-july14"
"sessions/july31/work/groups_set-04:0.00350093:0.01453356:0.00043983:july31/set-04:inherited-july14"
)

for row in "${ROWS[@]}"; do
  IFS=: read -r dir a b c setid prov <<<"$row"
  [ -d "$REPO/$dir" ] || { echo "skip (absent): $dir"; continue; }
  python3 - "$REPO" "$REPO/$dir" "$a" "$b" "$c" "$setid" "$prov" "$DRY" <<'PY'
import glob, json, os, sys
from astropy.io import fits            # HEADERS ONLY — no pixel access

repo, d, a, b, c, setid, prov, dry = sys.argv[1:9]
ses, sset = setid.split("/")
ds = os.path.join(repo, "datasets", ses, sset)


def load(p):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return {}


acq = load(os.path.join(ds, "acquisition.json"))
wh = (acq.get("exif") or {}).get("image_wh") or []
norm = min(int(wh[0]), int(wh[1])) / 2.0 if len(wh) == 2 else None
flat = load(os.path.join(ds, "qa_work", f"skyflat_{sset}_qa.json"))
fb = flat.get("build") or {}
fit = load(os.path.join(ds, "qa_work", "lens_fit.json"))
rho = (fit.get("control_point_coverage") or {}).get("rho_p99")

subs = sorted(glob.glob(os.path.join(d, "sub_*.fit")))
if not subs:
    print(f"skip (no sub_*.fit): {os.path.basename(d)}")
    sys.exit(0)
keys = {"DISTMODL": "ptlens", "DISTA": float(a), "DISTB": float(b), "DISTC": float(c),
        "CALSET": setid, "DISTSRC": f"backfill:{prov}"}
if norm:
    keys["DISTNORM"] = norm
if rho is not None:
    keys["DISTRHO"] = float(rho)
if fb.get("dark"):
    keys["CALDARK"] = os.path.basename(fb["dark"])[:68]
if flat.get("flat"):
    keys["CALFLAT"] = f"{os.path.basename(flat['flat'])}:{fb.get('frames','?')}"[:68]
if dry == "1":
    print(f"{os.path.basename(d)}: would stamp {len(subs)} sub-stack(s) with "
          + " ".join(f"{k}={v}" for k, v in keys.items()))
    sys.exit(0)
for s in subs:
    for k, v in keys.items():
        fits.setval(s, k, value=v, comment="backfilled provenance")
print(f"{os.path.basename(d)}: stamped {len(subs)} sub-stack(s)  [{prov}]")
PY
done
echo "backfill complete — DISTSRC carries backfill:<provenance> so a reconstructed"
echo "value is never mistaken for one stamped at warp time"
