#!/usr/bin/env bash
# Single source of truth for restoring the ACQUISITION FITS keywords that the
# undistort route's geometric warp drops, shared by every builder on that route
# (run_undistort_pipeline.sh, run_undistort_groups.sh) — the header counterpart
# to calibrate_light.sh and stack_rejection.sh.
#
# WHY THE KEYS ARE LOST. darktable cannot read FITS, so the warp stage is a
# round trip: Siril `savetif32` -> darktable -> Siril `convert`. A TIFF carries
# no FITS header, so every acquisition keyword Siril extracted from the raw
# (FOCALLEN, XPIXSZ/YPIXSZ, EXPTIME, APERTURE, ISOSPEED, INSTRUME, DATE-OBS)
# dies there. The loss is silent and it reaches the deliverable: `LIVETIME`
# lands at 0.0 because Siril's stack has no per-frame EXPTIME to accumulate,
# and the finished stack carries no plate scale, so solve_field.py loses its
# field-width hint and falls back to blind WIDE-FIELD index scales. That
# fallback still solved a 23 deg field (logodds 101); a narrow field cannot
# solve on those scales at all, so on a longer focal the same silent loss is a
# hard solve failure with a misleading cause.
#
# WHAT THIS DOES. Captures the keywords ONCE from a calibrated frame — while
# they still exist, before the warp — and restores them onto the finished stack
# with Siril's own `update_key`. Every value is Siril's: it read them from the
# raw and wrote them into the calibrated frame's header; nothing here derives a
# measurement. In-house code only READS the header (the one FITS access the
# bright line allows) and hands the values back to the tool.
#
#   header_capture <calibrated-frame.fit> <out.json>
#   header_stamp_lines <captured.json> <n_frames>   -> `update_key` lines
#
# The caller wraps the emitted lines in load/save, e.g.
#   printf 'requires 1.2.0\nsetcompress 0\nsetext fit\nload %s\n%s\nsave %s\n' ...
#
# LIVETIME is the one derived value: n_frames x EXPTIME, both tool-sourced (the
# stacked frame count the builder holds, and Siril's own EXPTIME). It is the
# integration time the stack actually represents; Siril cannot recompute it
# because the per-frame EXPTIME it would sum was destroyed upstream.
#
# BAYERPAT is deliberately NOT restored: the stack is debayered RGB, and a
# Bayer pattern on an RGB image would make a downstream consumer treat it as a
# mosaic.
#
# REMOVAL CONDITION: the warp stage stops being a TIFF round trip (darktable
# gains FITS I/O, or the distortion is consumed natively — Siril `register
# -disto=`, BACKLOG item 7), so the keywords are never dropped and there is
# nothing to restore.

# PROVENANCE STAMP (the second half of this file). A sub-stack that will be
# composed months from now must answer "what warped you, what calibrated you"
# with NO external lookup, no machine state, and no memory of the session that
# made it — because the lensfun user DB is global, unscoped, single-valued
# machine state that nothing reverts, so "the model this set's record names" is
# only true while that record is the one installed.
#
# MEASURED cost of not having this: three aug06 sets were warped under three
# different distortion models and composed into one union. The models diverge by
# up to 8.19 px through the production warp; after registration the members
# disagree by 2.99 px at the composed corner (0.93 px for the SAME member pair
# under one model), which the mean renders as doubled stars. Nothing in the
# product, the sub-stacks, or the compose could see it — the sub-stacks carried
# no optics provenance at all, so the compose had nothing to assert on.
#
# The coefficients come from `lens_preflight.json`, i.e. what was VERIFIED LIVE
# in the DB at build time — never from `lens_fit.json`, which is what the set
# INTENDED. Stamping the intention would re-create the class of bug this stamp
# exists to close.
#
# Keys copied verbatim from the calibrated frame. Order is the write order.
_STAMP_KEYS="FOCALLEN XPIXSZ YPIXSZ EXPTIME APERTURE ISOSPEED INSTRUME DATE-OBS"

header_capture() {  # <calibrated-frame.fit> <out.json>
  local src=$1 out=$2
  [ -f "$src" ] || { echo "header_capture: no such frame: $src" >&2; return 1; }
  python3 - "$src" "$out" "$_STAMP_KEYS" <<'PY'
import json, sys
from astropy.io import fits          # header READ only — no pixel access
src, out, keys = sys.argv[1], sys.argv[2], sys.argv[3].split()
h = fits.getheader(src)
rec = {k: h[k] for k in keys if k in h}
rec["_source"] = src
json.dump(rec, open(out, "w"), indent=1)
print(f"header_capture: {len(rec)-1} acquisition keyword(s) from {src.split('/')[-1]}")
PY
}

header_stamp_lines() {  # <captured.json> <n_frames>  -> siril update_key lines
  local rec=$1 n=$2
  [ -f "$rec" ] || { echo "header_stamp_lines: no capture record: $rec" >&2; return 1; }
  python3 - "$rec" "$n" "$_STAMP_KEYS" <<'PY'
import json, sys
rec, n, keys = json.load(open(sys.argv[1])), int(sys.argv[2]), sys.argv[3].split()
out = []
for k in keys:
    if k in rec:
        v = rec[k]
        out.append(f'update_key {k} "{v}"' if isinstance(v, str) else f"update_key {k} {v}")
if "EXPTIME" in rec:                      # the integration the stack represents
    out.append(f"update_key LIVETIME {round(n * float(rec['EXPTIME']), 3)}")
print("\n".join(out))
PY
}

# header_provenance_lines <repo> <session-dir> <set> [<bkglight>]  -> update_key lines
#
# The optics + calibration identity, read from the SET'S OWN TRACKED RECORDS and
# handed to Siril's own update_key. Emits nothing and returns 0 when a record is
# missing a field — a partial stamp is better than none, and every consumer
# treats an absent key as "unknown", never as "compatible".
#
#   DISTMODL/DISTA/DISTB/DISTC  the distortion model VERIFIED LIVE in the lensfun
#                               DB at build time (lens_preflight.json)
#   DISTNORM                    the normalisation radius in px, min(W,H)/2 —
#                               MEASURED: lensfun normalises ptlens by HALF THE
#                               SHORT SIDE (probe RMS 4.47 px against 18.3 for
#                               half-long-side and 22.2 for half-diagonal), so the
#                               frame corner sits at rho = 1.80 and a reader does
#                               not have to re-derive the convention to know it
#   DISTRHO                     the fit's control-point support ceiling (p99 rho).
#                               MEASURED census: every fit ever shipped here stops
#                               at 1.47-1.51 against a corner at 1.80, so this is
#                               the number that says whether the corner was FITTED
#                               or EXTRAPOLATED
#   DISTSRC / DISTFIT           where the MODEL came from — the pinned registry key
#                               and the frames+commit it was fitted from. NOT the
#                               set that used it: the model is a property of the
#                               lens and optical state, and a per-set lens_fit.json
#                               is a CANDIDATE until promoted into the registry
#   CALSET / CALDARK / CALFLAT  the set, and the masters' identity + depth
#   BKGLIGHT                    the LIGHTS-SIDE BACKGROUND TREATMENT: `none`, or
#                               `subsky1-nodither` when --subsky-lights ran a
#                               per-frame degree-1 subtraction before the warp.
#                               A member's background state is a processing state
#                               exactly like its optical state, and a combine that
#                               mixes them is mixing two different sky baselines —
#                               so it has to be VISIBLE to the gate, not inferable
#                               only from which work dir the file came out of.
#   DISTPROV                    `stamped` (written at warp time, from the model
#                               verified live in the DB) or `backfill` (reconstructed
#                               later from the committed records). Machine-readable,
#                               because a prefix buried in a free-text field is not
#                               something a gate can be relied on to parse.
#   PIPEREV                     the repo commit the build ran under
header_provenance_lines() {  # <repo> <session-dir> <set> [<bkglight>]
  python3 - "$1" "$2" "$3" "${4:-none}" <<'PY'
import json, os, subprocess, sys
repo, session, sset, bkglight = sys.argv[1:5]
ses = os.path.basename(os.path.abspath(session))
d = os.path.join(repo, "datasets", ses, sset)
out = []


def load(p):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return {}


def key(k, v):
    if v is None or v == "":
        return
    out.append(f'update_key {k} "{v}"' if isinstance(v, str)
               else f"update_key {k} {v}")


pre = load(os.path.join(d, "qa_work", "lens_preflight.json"))
sm = pre.get("state_model") or pre.get("pinned_model") or {}
co = sm.get("coefficients") or sm.get("installed") or {}
if co:
    key("DISTMODL", "ptlens")
    for k in "abc":
        key("DIST" + k.upper(), float(co[k]))
acq = load(os.path.join(d, "acquisition.json"))
wh = (acq.get("exif") or {}).get("image_wh") or []
if len(wh) == 2:
    key("DISTNORM", min(int(wh[0]), int(wh[1])) / 2.0)

# DISTSRC names where the MODEL came from, never which set happened to use it —
# the model is a property of the lens and optical state, and the authority is the
# repo-global pinned registry. A per-set lens_fit.json is a CANDIDATE fit and is
# not stamped as the source unless it was promoted into the registry.
models = load(os.path.join(repo, "scripts", "darktable", "lens_models.json"))
mkey = next((k for k in models if k != "_readme" and not k.startswith("_")
             and str(sm.get("key", "")).lower() == k.lower()), None)
if mkey is None:
    mkey = next((k for k in models if not k.startswith("_")), None)
ent = models.get(mkey) or {}
fitted = ent.get("fitted") or {}
if mkey:
    key("DISTSRC", f"pinned:{mkey}"[:68])
    key("DISTFIT", f"{fitted.get('from','?')}@{fitted.get('commit','?')}"[:68])
cov = (ent.get("control_point_coverage") or {})
key("DISTRHO", cov.get("rho_p99"))

key("CALSET", f"{ses}/{sset}")
key("BKGLIGHT", bkglight)
key("DISTPROV", "stamped")
flat = load(os.path.join(d, "qa_work", f"skyflat_{sset}_qa.json"))
b = flat.get("build") or {}
if b.get("dark"):
    key("CALDARK", os.path.basename(b["dark"])[:68])
if flat.get("flat"):
    key("CALFLAT", f"{os.path.basename(flat['flat'])}:{b.get('frames', '?')}"[:68])
try:
    rev = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    key("PIPEREV", rev)
except OSError:
    pass
print("\n".join(out))
PY
}
