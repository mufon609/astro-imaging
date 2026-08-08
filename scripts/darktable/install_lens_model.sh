#!/usr/bin/env bash
# Install a SET'S OWN optical-state distortion model into the live lensfun
# user DB (the one darktable reads).
#
#   install_lens_model.sh <session-dir> <set> [--replace]   the standing form
#   install_lens_model.sh --lens M --focal F a b c          explicit coefficients
#
# THE AUTHORITY IS THE SET'S OWN RECORD — `qa_work/lens_fit.json`: fitted
# from the set's frames (fit_lens_model.sh), or explicitly INHERITED
# (`inherited_from` provenance) where the set's own fit is untrustworthy.
# The model keys on the OPTICAL STATE, per set: focus recalibrates every
# session, sometimes mid-night, and five fitted states measured pairwise all
# exceed the 0.47 px displacement-equivalence bound
# (BACKLOG:`optical-state-models`; the set-01 own-model rebuild removed a 2x
# field-term elevation the shared model caused). A repo-global pinned model
# (`lens_models.json`) was the prior method and is REMOVED — one model per
# lens@focal can be right for at most one state per night.
# A fitted model is still a measured CONSTANT: reproduce it by installing
# the record's coefficients, never by re-fitting (a re-fit is a NEW model —
# measured, same frames + different Hugin = 3.9%/30.6% apart).
#
# The lens and focal are read from the set's own `acquisition.json`
# (`exif.lens`, `exif.focal_length_mm`). Nothing about a body is hardcoded.
#
# Why a fitted entry replaces the community one: on this rig's 24-70/4 S the
# community ptlens profile agreed at the field corner (0.06 px at r=2664) but
# diverged 2.4-3.9 px through the paraxial/mid region. On a far-drifting
# untracked set that error is crossed by the optical axis and smears an
# along-drift band through frame centre; with the fitted entry the centre station
# sits at the in-exposure floor and the whole frame sharpens (docs/dead-ends.md,
# paraxial-band entry). That is a property of community profiles in general, not
# of one lens — re-fit per lens/body/focal.
#
# This script also STRIPS <vignetting> and <tca> from that lens's block. That is
# what makes the warp DISTORTION-ONLY: darktable ignores a style's lens op_params
# (only the enabled bit carries) and applies its default correction set, so the
# correction set can only be chosen in the data lensfun reads. Vignetting
# correction here would double-correct lights already flat-corrected upstream
# (docs/dead-ends.md).
#
# The target is the machine-local lensfun updates DB
# (~/.local/share/lensfun/updates/version_1), written by `lensfun-update-data`,
# which the route already requires per rig. The DB FILE is found by searching
# that directory for the lens — vendor file names (mil-nikon.xml, slr-canon.xml,
# compact-*.xml …) are lensfun's business, not ours. `lensfun-update-data`
# OVERWRITES this patch: re-run after any DB update.
#
# SAFETY: the edit records the COEFFICIENTS it replaced in an XML comment inside
# the block, so the patch is self-describing and reversible, and a block already
# carrying a marker with DIFFERENT coefficients STOPS rather than being silently
# overwritten — a re-fit is an explicit act. (Comments inside <lens> are known
# safe: upstream ships them, e.g. "<!-- Taken with Nikon Z6 -->".)
# The marker records `replaced a=… b=… c=…` and NOT the verbatim
# `<distortion .../>` element it used to embed. That element was a DECOY: it put
# a second parseable copy of a distortion line inside the same <lens> block, and
# every raw-text scanner — the idempotence test and the replace target here, and
# lens_preflight.py's installed-vs-pinned assertion — matched the comment's copy
# before the live one. MEASURED 2026-08-05: the assertion reported the pinned
# model installed while lensfun was applying a different one, and this script
# reported "already installed" (with --replace too), so the DB could not be
# restored by any documented invocation. Recording coefficients keeps the
# provenance and removes the second copy, which is cheaper than masking and
# cannot regress; live() below still masks comments so a block written by an
# older version of this script is handled too.
#
# Verify after any darktable/lensfun version change with verify_lens_card.py
# (grid positive control + uniform card; the card ALONE is vacuous).
#
# Removal conditions: an upstream lensfun entry measured for THIS unit at
# infinity focus, or a chain that consumes the model another way (Siril
# `register -disto=` with a trustworthy source). The vignetting/tca strip retires
# when darktable honours a style's lens op_params headless. Both are registered
# in BACKLOG.md `removal-conditions`.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
DBDIR="$HOME/.local/share/lensfun/updates/version_1"

LENS= FOCAL= SESSION= SET= REPLACE=0 ABC=()
if [ "${1:-}" = "--lens" ] || [ "${1:-}" = "--focal" ]; then
  while [ $# -gt 0 ]; do case "$1" in
    --lens) LENS=$2; shift 2;;
    --focal) FOCAL=$2; shift 2;;
    --replace) REPLACE=1; shift;;
    *) ABC+=("$1"); shift;;
  esac; done
else
  SESSION=${1:?usage: install_lens_model.sh <session-dir> <set> [--replace]  |  --lens M --focal F a b c}
  SET=${2:?missing <set>}
  shift 2
  while [ $# -gt 0 ]; do case "$1" in
    --replace) REPLACE=1; shift;;
    *) ABC+=("$1"); shift;;
  esac; done
fi
[ ${#ABC[@]} -eq 0 ] || [ ${#ABC[@]} -eq 3 ] || {
  echo "install_lens_model: pass all three of a b c, or none (then the fit record supplies them)" >&2; exit 1; }
[ -d "$DBDIR" ] || { echo "install_lens_model: $DBDIR missing — run lensfun-update-data first" >&2; exit 1; }

python3 - "$REPO" "$DBDIR" "${SESSION:-}" "${SET:-}" "$LENS" "$FOCAL" "$REPLACE" "${ABC[@]}" <<'PY'
import glob, json, os, re, sys
from datetime import date


def live(s):
    """Blank the CONTENT of XML comments, preserving length so match offsets
    still index the original string. EVERY scan for a live element must go
    through this, because the marker this script writes embeds a VERBATIM
    `<distortion .../>` element (it records what it replaced) — so a raw
    substring or regex scan finds the marker's copy before the real line.
    MEASURED cost of not doing it, on this rig 2026-08-05: the idempotence
    test `new_line in block` matched the pinned coefficients inside the
    marker while the live line carried a different (candidate) model, so the
    installer reported "already installed" and exited 0 — with --replace too,
    since that branch is downstream. The DB could not be restored to the
    pinned model by any documented invocation, and lens_preflight.py's
    installed-vs-pinned assertion (same blind scan) reported OK on the wrong
    optics. lensfun ignores comments; the guards must too."""
    return re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), s, flags=re.S)

repo, dbdir, session, sset, lens, focal, replace = sys.argv[1:8]
abc = sys.argv[8:]
replace = replace == "1"

# ---- identity + coefficients from the SET'S OWN RECORDS ------------------
if session:
    d = os.path.join(repo, "datasets", os.path.basename(os.path.abspath(session)), sset)
    acq_p = os.path.join(d, "acquisition.json")
    try:
        acq = json.load(open(acq_p))
    except (OSError, ValueError) as e:
        sys.exit(f"install_lens_model: no usable acquisition record at {acq_p} ({e}) "
                 "— the lens identity comes from the set's record, so this STOPS "
                 "rather than assume a lens.")
    ex = acq.get("exif") or {}
    lens = lens or (ex.get("lens") or "")
    focal = focal or (ex.get("focal_length_mm") or "")
    if not lens:
        sys.exit(f"install_lens_model: {acq_p} records no exif.lens. A telescope/"
                 "astrocam set has no lens EXIF by construction and does not take "
                 "the lens-correction route at all.")
    if not abc:
        fit_p = os.path.join(d, "qa_work", "lens_fit.json")
        try:
            rec = json.load(open(fit_p))
            fit = rec["fitted_ptlens"]
        except (OSError, ValueError, KeyError) as e:
            sys.exit(f"install_lens_model: no optical-state record at {fit_p} ({e}).\n"
                     "  The model is PER-SET (BACKLOG:optical-state-models): fit it —\n"
                     "    scripts/darktable/fit_lens_model.sh <session> <set> --dark=... --flat=... --hfov=...\n"
                     "  or write a lens_fit.json with `inherited_from` provenance where the set's\n"
                     "  own fit is untrustworthy. A set never installs a model that is not its record.")
        abc = [repr(float(fit[k])) for k in ("a", "b", "c")]
        source = ("SET RECORD " + fit_p +
                  (" (inherited: " + rec["inherited_from"] + ")"
                   if rec.get("inherited_from") else " (fitted from this set's own frames)"))
if not lens or focal in ("", None):
    sys.exit("install_lens_model: need a lens and a focal (from the set's record, "
             "or --lens/--focal).")

# ---- the SET RECORD is the authority; --lens form requires explicit abc ---
def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

f0 = float(focal)
focal_key = str(int(f0)) if f0 == int(f0) else str(f0)
key = f"{lens}@{focal_key}"
if not abc:
    sys.exit("install_lens_model: the --lens/--focal form needs explicit "
             "coefficients (a b c). The standing form reads the SET's own "
             "record: install_lens_model.sh <session-dir> <set>.")
if "source" not in dir():
    source = "explicit coefficients on the command line"
focal_s = str(int(f0)) if f0 == int(f0) else str(f0)   # lensfun writes focal="70"
a, b, c = abc

# ---- find the lens block, by CONTENT not by file name ---------------------
target = norm(lens)
hits = []
for path in sorted(glob.glob(os.path.join(dbdir, "*.xml"))):
    try:
        xml = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        continue
    for m in re.finditer(r"<lens>(?:(?!</lens>).)*?</lens>", xml, re.S):
        mm = re.search(r"<model>(.*?)</model>", m.group(0), re.S)
        if mm and norm(mm.group(1)) == target:
            hits.append((path, m.group(0), mm.group(1)))
if not hits:
    sys.exit(f"install_lens_model: no <lens> block in {dbdir} whose <model> matches "
             f"{lens!r}. lensfun's spelling can differ from the EXIF string — check "
             "`grep -ri '<model>' " + dbdir + "` and pass --lens with the DB's "
             "spelling, or run lensfun-update-data if the lens is simply absent.")
if len(hits) > 1:
    where = ", ".join(f"{os.path.basename(p)}" for p, _, _ in hits)
    sys.exit(f"install_lens_model: {len(hits)} lens blocks match {lens!r} ({where}) "
             "— refusing to guess which one darktable will pick.")
path, block, db_model = hits[0]
xml = open(path, encoding="utf-8", errors="replace").read()

MARK = "astro-imaging fitted:"
new_line = (f'<distortion model="ptlens" focal="{focal_s}" '
            f'a="{a}" b="{b}" c="{c}"/>')

prior = re.search(rf"<!--\s*{MARK}\s*focal={focal_s}\s+(.*?)-->", block, re.S)
# `prior` reads the MARKER, so it scans the raw block; every test below asks
# what lensfun will actually apply, so it scans live(block) — see live().
if new_line in live(block) and prior:
    print(f"install_lens_model: already installed for {db_model} @ {focal_s}mm "
          f"({os.path.basename(path)})")
    sys.exit(0)
if prior and new_line not in live(block) and not replace:
    sys.exit(f"install_lens_model: {db_model} @ {focal_s}mm already carries a "
             f"DIFFERENT fitted entry ({prior.group(1).strip()}).\n"
             "  Swapping the installed model is an explicit act — pass --replace.\n"
             "  That is the A/B workflow (install a candidate with --from-fit "
             "--replace, measure it, then restore the pinned model with a plain "
             "install), and it is how a promotion is done too. Without the flag "
             "nothing is overwritten.")

existing = re.search(rf'<distortion[^>]*focal="{re.escape(focal_s)}"[^>]*/>',
                     live(block))
if existing:
    # splice by OFFSET, not str.replace: replace() is global, so with the
    # marker's verbatim copy in the block it would rewrite the marker's text
    # (and, when the two happened to agree, both) instead of the one live line.
    new_block = block[:existing.start()] + new_line + block[existing.end():]
    # Record the replaced COEFFICIENTS, never the verbatim element. The marker
    # used to embed the whole `<distortion .../>` tag for self-description, and
    # that decoy is what defeated every scanner in this file and in
    # lens_preflight.py. Provenance is preserved; the second parseable copy is
    # not created in the first place, so a future scanner cannot be fooled by it
    # even if it forgets to mask comments. live() stays as defence for blocks
    # already carrying an old-style marker.
    old = dict(re.findall(r'\b([abc])="([-0-9.eE+]+)"',
                          block[existing.start():existing.end()]))
    what = ("replaced " + " ".join(f"{k}={old[k]}" for k in "abc" if k in old)
            if old else "replaced (unparseable prior line)")
else:                                   # a focal the DB never carried
    if "<calibration>" not in block:
        sys.exit(f"install_lens_model: {db_model} has no <calibration> block to "
                 "add a distortion line to — reconcile upstream.")
    new_block = block.replace("<calibration>",
                              "<calibration>\n            " + new_line, 1)
    what = f"added (no focal={focal_s} line upstream)"

# distortion-only enforcement: strip this lens's vignetting/tca
n_strip = len(re.findall(r"<(?:vignetting|tca)\b", new_block))
new_block = re.sub(r"\s*<(?:vignetting|tca)\b[^>]*/>", "", new_block)
if "<distortion" not in live(new_block):
    sys.exit("install_lens_model: the edit would leave no distortion model — refusing.")

marker = (f'<!-- {MARK} focal={focal_s} {what}; '
          f'{"from " + os.path.basename(os.path.abspath(session)) + "/" + sset + "; " if session else ""}'
          f'vignetting+tca stripped ({n_strip}); {date.today().isoformat()} -->')
if prior:            # swapping this focal: replace its marker, do not stack another
    new_block = re.sub(rf"\s*<!--\s*{MARK}\s*focal={re.escape(focal_s)}\s.*?-->",
                       "", new_block, flags=re.S)
new_block = new_block.replace("<calibration>", marker + "\n        <calibration>", 1)

open(path, "w", encoding="utf-8").write(xml.replace(block, new_block))
print(f"install_lens_model: {db_model} @ {focal_s}mm — {what}")
print(f"  source: {source}")
print(f"  a={a} b={b} c={c}")
print(f"  stripped {n_strip} vignetting/tca entries — distortion-only holds")
print(f"  {path}")
PY
