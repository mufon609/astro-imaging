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
# -disto=`, BACKLOG:`native-solve-and-sip`), so the keywords are never dropped
# and there is
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
header_provenance_lines() {  # <repo> <session-dir> <set> [<bkglight>] [<ran-dark>] [<ran-flat>]
  python3 - "$1" "$2" "$3" "${4:-none}" "${5:-}" "${6:-}" <<'PY'
import json, os, subprocess, sys
repo, session, sset, bkglight, ran_dark, ran_flat = sys.argv[1:7]
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


def master_facts(path):
    """(frames, datasum) from the master's own file. Reads the data block ONCE
    to hash it (`add_datasum()` computes over the data bytes) and NEVER
    writes: the sum lands in the in-memory header only, and the file is not
    saved. Siril strips DATASUM/CHECKSUM on any load+save (measured), which
    is why the hash is carried on the PRODUCT as a provenance value rather than
    embedded in the master — ESO's `CAL1 NAME` + `CAL1 DATAMD5` shape."""
    try:
        from astropy.io import fits
        with fits.open(path) as hl:
            n = hl[0].header.get("STACKCNT", "?")
            hl[0].add_datasum()
            return n, str(hl[0].header.get("DATASUM", ""))
    except Exception:
        return "?", ""


# WHICH MASTER THE KEYS DESCRIBE. The set's RECORD is right for every ordinary
# build and WRONG the moment `--flat` names another master: the product then
# claims a calibration it never got. The masters that RAN are passed in by the
# builder; the record is the fallback for a caller that does not pass them, and
# CALPROV says which happened rather than leaving the two indistinguishable — a
# schema change without both sides labelled leaves a silent generation boundary.
dark_path = ran_dark or b.get("dark")
flat_path = ran_flat or flat.get("flat")
key("CALPROV", "ran" if (ran_dark or ran_flat) else "record")
if dark_path:
    key("CALDARK", os.path.basename(dark_path)[:68])
    if ran_dark:
        _, dsum = master_facts(dark_path)
        if dsum:
            key("CALDSUM", dsum)
if flat_path:
    if ran_flat:
        nfr, fsum = master_facts(flat_path)
        key("CALFLAT", f"{os.path.basename(flat_path)}:{nfr}"[:68])
        if fsum:
            key("CALFSUM", fsum)
    else:
        key("CALFLAT", f"{os.path.basename(flat_path)}:{b.get('frames', '?')}"[:68])
try:
    rev = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    key("PIPEREV", rev)
except OSError:
    pass
print("\n".join(out))
PY
}

# header_registration_lines <astrometric|starpair> <T|F>  -> update_key lines
#
# WHAT REGISTERED IT, recorded ON the product. Nothing in a FITS header said
# whether a composite was aligned by star-pair homography or by each member's own
# plate solution, and the difference is the largest defect this project has
# shipped: MEASURED on the 28-member union at RA 294.86, `register -2pass` reads
# roundness 0.458 where `seqplatesolve` reads 0.974. Working out which a product
# used cost a day of dating files and reading build logs. It is one key.
#
#   REGMODEL  `astrometric` (per-member, from each member's own WCS) or
#             `starpair` (one homography per member fitted to matched stars)
#   REGUNDIS  T when siril reported applying per-member SIP undistortion, F when
#             it did not. Sourced from the tool's OWN log, never assumed: the
#             route silently degrades to a linear map when a member lacks SIP.
# header_registration_lines <model> <undistorted T|F> [<ref-id>] [<ref-source>]
#
# REGREF / REGREFSR PUT THE RESOLVED REGISTRATION REFERENCE ON THE ARTIFACT.
# WHY, MEASURED RATHER THAN ARGUED: the composite recorded which MODEL registered
# it and never which MEMBER it registered AGAINST, and the compose deletes its
# scratch (`rm -rf "$W"`) so the `.seq` that held the answer does not outlive the
# run. The cost of that gap, in one episode: a tracked record asserted the wrong
# mechanism for the auto-pick ("ranks over the whole member pool" — it takes
# index 0), it was reported to the owner as a defect, the truth had to be
# reconstructed from `compose_gate_*.json` files that survived only because they
# are written OUTSIDE the scratch dir, and the tracked field was revised twice.
# A stamped reference makes all of that one header read.
#
# It is siril's OWN reference, parsed from the `.seq` it wrote, not the value the
# caller asked for — so it is true under `auto`, where nothing was asked.
# REGREFSR records how it got there: pinned (operator --ref) | derived (the
# chain's rule) | auto (siril chose, nothing determined it).
#
# PRODUCTS BUILT BEFORE THIS CHANGE CARRY NO REGREF, AND THAT IS EXPECTED — they
# are NOT backfilled. Writing a header onto an accepted product is a byte-change
# to a deliverable for tidiness, which does not earn the declared-delta the
# contract requires, and `baseline_guard.py` compares products. Their reference
# is not lost: `datasets/corpus/corpus4_build_record.json` records it (s_00001,
# evidenced by ten `compose_gate_*.json` records and a probe whose positive
# control measured 0 differing pixels of 98,194,977 between the auto arm and an
# explicit --ref=1). Look there rather than re-deriving it.
#
# THE CHAIN ENDS AT THE FITS. The judge PNG — the only surface a verdict may be
# taken on — carries none of this, because PNG has no header. Provenance is
# recoverable from the FITS beside it, never from the image a human looks at.
header_registration_lines() {  # <model> <undistorted T|F> [<ref-id>] [<ref-source>]
  printf 'update_key REGMODEL "%s"\nupdate_key REGUNDIS "%s"\n' "$1" "$2"
  [ -n "${3:-}" ] && printf 'update_key REGREF "%s"\n' "$3"
  [ -n "${4:-}" ] && printf 'update_key REGREFSR "%s"\n' "$4"
  return 0
}

# header_composite_provenance_lines <member.fit>...  -> update_key lines
#
# THE COMPOSITE'S OWN IDENTITY, not the reference member's. siril's `stack`
# propagates the header of the reference image, so a 28-member cross-night union
# INHERITED `CALSET = july31/set-01` and `CALFLAT = skyflat_set-01.fit:507` —
# asserting one set's calibration identity for a composite of six sets across two
# nights. That is worse than an absent stamp: a gate reading it is told a
# confident falsehood. (STACKCNT/LIVETIME are summed correctly by siril and are
# left alone.)
#
# Emits the value where every member AGREES, and `MIXED(<n>)` where they do not,
# so a mixed composite is visible rather than inferable. Adds:
#   NMEMBER   how many members went in
#   CALSETS   the distinct sets, comma-joined, truncated to the 68-char FITS
#             string limit with a trailing "+N" when it does not fit
#   PROVMIX   T when any provenance key differs across members
#   PIPEREV   the commit the COMPOSE ran under — left inherited it reads the
#             reference member's build rev instead (measured on both corpora:
#             datasets/corpus/piperev_inheritance.json)
#   DATE-OBS  the EARLIEST member start (FITS convention: start of observation;
#             equals the ISO of the EXPSTART siril writes) — left inherited it
#             reads the reference SET's start, false for a multi-night product
# and DELETES GRPSIZE + FILENAME: single-member facts (one group's size,
# siril's scratch name) that are false-by-construction on a composite.
# CALSET rides the KEYS tuple like its siblings (common value or MIXED(n)) —
# otherwise the SINGULAR key survives from the reference, which is the exact
# falsehood the worked example above describes.
header_composite_provenance_lines() {  # <repo> <member.fit>...
  python3 - "$@" <<'PY2'
import os, subprocess, sys
try:
    from astropy.io import fits
except ImportError:
    sys.exit(0)
# CALFSUM/CALDSUM ARE IN THIS TUPLE DELIBERATELY, and it is the half that closes
# the defect. A basename cannot distinguish two masters — 19 flats under 12
# basenames here, `dark_master.fit` identical across all three sessions — so a
# cross-night union's `uniq` over CALFLAT collapses three different masters to
# ONE value and the composite reports agreement where there is none. The content
# hashes do not collide, so the same `uniq` reports MIXED. A provenance key
# absent from this tuple is half-shipped.
KEYS = ("DISTMODL", "DISTA", "DISTB", "DISTC", "DISTNORM", "DISTRHO",
        "DISTSRC", "DISTFIT", "CALDARK", "CALFLAT", "CALDSUM", "CALFSUM",
        "CALPROV", "BKGLIGHT", "DISTPROV", "CALSET")
repo = sys.argv[1]
members = sys.argv[2:]
vals = {k: [] for k in KEYS}
sets = []
dates = []
for m in members:
    try:
        h = fits.getheader(m)
    except Exception:
        continue
    for k in KEYS:
        if k in h:
            vals[k].append(h[k])
    if "CALSET" in h:
        sets.append(str(h["CALSET"]))
    if "DATE-OBS" in h:
        dates.append(str(h["DATE-OBS"]))
out = ["update_key NMEMBER %d" % len(members)]
mixed = False
# THE PORTION-RULE STAGE'S KEYS (run_member_crop.sh). A stage-cropped copy carries
# MEMCROP (int x_c px), MEMCRULE, MEMCPROV, MEMCSCOR; an untouched member carries
# none. The GO #12/#13 ARM copies predate the stage and carry MEMCROP as a PROSE
# string with none of the other three ("entry cols beyond +1500 px removed (...)")
# — LEGACY. Behaviour, ruled:
#   NCROPPED  stamped on EVERY composite this emitter stamps: 0 = "composed under
#             this code, nothing cropped"; the key's ABSENCE marks a composite
#             stamped before the stage existed. It does NOT distinguish
#             "--portion-rule not used" from "used, cropped nothing" — both stamp
#             0; the stage RECORD carries that fact.
#   MEMCROP   a non-int (legacy) value counts in NCROPPED and never crashes this
#             emitter; all-legacy stamps MEMCRULE "LEGACY(n)"; legacy mixed with
#             structured joins the REFUSED path below with the legacy count named.
#   MEMCXCS   the x_c histogram over the STRUCTURED crops only (legacy carry no int).
#   MEMCRULE  the ONE rule the cropped members were cropped under, or
#             "REFUSED:MIXED(n)" when their rule identities disagree — the refusal
#             IS the stamp (plus stderr + exit 1): a hard stop is the CALLER's
#             check, because the compose applies whatever lines were printed
#             (header_apply_keys consumes this emitter inside $(), where the exit
#             status dies). Stated, not hidden.
crops = []            # (x_c int | None, rule, prov); x_c None = legacy prose MEMCROP
for m in members:
    try:
        h = fits.getheader(m)
    except Exception:
        continue
    if "MEMCROP" not in h:
        continue
    try:
        xc = int(str(h["MEMCROP"]).strip())
    except (TypeError, ValueError):
        xc = None
    crops.append((xc, str(h.get("MEMCRULE", "")), str(h.get("MEMCPROV", ""))))
out.append("update_key NCROPPED %d" % len(crops))
if crops:
    structured = [c for c in crops if c[0] is not None]
    n_legacy = len(crops) - len(structured)
    hist = {}
    for xc, _, _ in structured:
        hist[xc] = hist.get(xc, 0) + 1
    if hist:
        out.append('update_key MEMCXCS "%s"' % "/".join("%dx%d" % (xc, n) for xc, n in sorted(hist.items(), reverse=True))[:68])
    provs = list(dict.fromkeys(p for _, _, p in structured if p))
    if provs:
        out.append('update_key MEMCPROV "%s"' % (provs[0] if len(provs) == 1 else "MIXED(%d)" % len(provs))[:68])
    rules = list(dict.fromkeys(r for _, r, _ in structured if r))
    if any(not r for _, r, _ in structured):
        rules.append("UNSTATED(%d)" % sum(1 for _, r, _ in structured if not r))
    if n_legacy:
        rules.append("LEGACY(%d)" % n_legacy)
    if len(rules) == 1:
        out.append('update_key MEMCRULE "%s"' % rules[0][:68])
    else:
        out.append('update_key MEMCRULE "REFUSED:MIXED(%d)"' % len(rules))
        print("\n".join(out))
        print("REFUSED: the cropped members carry %d rule identities (%s) — one rule per compose; the refusal is in the stamp" % (len(rules), "; ".join(rules)), file=sys.stderr)
        sys.exit(1)
for k in KEYS:
    v = vals[k]
    if not v:
        continue
    uniq = list(dict.fromkeys(v))
    if len(uniq) == 1:
        x = uniq[0]
        out.append('update_key %s "%s"' % (k, x) if isinstance(x, str)
                   else "update_key %s %s" % (k, x))
    else:
        mixed = True
        out.append('update_key %s "MIXED(%d)"' % (k, len(uniq)))
uniq_sets = list(dict.fromkeys(sets))
if uniq_sets:
    joined, dropped = "", 0
    for i, x in enumerate(uniq_sets):
        cand = (joined + "," + x) if joined else x
        if len(cand) <= 62:
            joined = cand
        else:
            dropped = len(uniq_sets) - i
            break
    if dropped:
        joined += "+%d" % dropped
    out.append('update_key CALSETS "%s"' % joined)
    if len(uniq_sets) > 1:
        mixed = True
out.append('update_key PROVMIX "%s"' % ("T" if mixed else "F"))
if dates:
    out.append('update_key DATE-OBS "%s"' % min(dates))
try:
    rev = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    if rev:
        out.append('update_key PIPEREV "%s"' % rev)
except OSError:
    pass
out.append("delete_key GRPSIZE")
out.append("delete_key FILENAME")
print("\n".join(out))
PY2
}

# header_apply_keys <file.fit> <update_key-lines>
#
# WHY THIS EXISTS — a MEASURED silent truncation that would have corrupted every
# provenance stamp in a rebuild. Siril's `update_key` builds the FITS card as
# text, and `/` BEGINS THE COMMENT FIELD in a FITS card, so a string value
# containing a slash is cut at the slash with no error:
#
#     update_key K1 "aug06/set-01"          -> stored as 'aug06'
#     update_key K3 "a/b,c/d"               -> stored as 'a'
#     update_key K4 "aug06_set-01+july31"   -> intact (no slash)
#
# CALSET is `<session>/<set>` by construction, so every stamp written through
# siril loses the set and claims the whole session. The existing corpus escaped
# only because `backfill_substack_provenance.sh` wrote its keys with astropy
# `fits.setval` instead — the same header-only mechanism used here, and the
# repo's own precedent for writing provenance (headers only, no pixel access).
#
# Takes the emitters' `update_key K V` lines unchanged so call sites keep one
# vocabulary, and applies them with a FITS library that quotes properly.
header_apply_keys() {  # <file.fit> <lines>
  python3 - "$1" "$2" <<'PY2'
import shlex, sys
from astropy.io import fits                 # HEADERS ONLY — no pixel access
path, block = sys.argv[1], sys.argv[2]
with fits.open(path, mode="update") as hd:
    h = hd[0].header
    for line in block.splitlines():
        parts = shlex.split(line.strip())
        if len(parts) == 2 and parts[0] == "delete_key":
            h.pop(parts[1], None)
            continue
        if len(parts) < 3 or parts[0] != "update_key":
            continue
        k, v = parts[1], " ".join(parts[2:])
        if v in ("T", "F"):
            h[k] = (v == "T")
            continue
        try:
            h[k] = int(v) if v.lstrip("+-").isdigit() else float(v)
        except ValueError:
            h[k] = v[:68]
PY2
}
