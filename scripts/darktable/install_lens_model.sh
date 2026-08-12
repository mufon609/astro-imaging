#!/usr/bin/env bash
# Install a MEASURED distortion model into the live lensfun user DB (the one
# darktable reads), for the lens and focal a given SET was actually shot with.
#
#   install_lens_model.sh <session-dir> <set>            install the PINNED model
#   install_lens_model.sh --lens "<model>" --focal <mm>   same, named explicitly
#   install_lens_model.sh <session-dir> <set> --from-fit  install that set's FRESH fit
#   install_lens_model.sh --lens M --focal F a b c        explicit coefficients
#   … --center X,Y     ALSO write lensfun's <center> (a DECENTRING knob, opt-in,
#                      per-LENS not per-focal; --center 0,0 removes it)
#
# THE AUTHORITY IS `scripts/darktable/lens_models.json`, not a dataset. A fitted
# model is a property of the LENS AND FOCAL, and it is a measured CONSTANT: you
# reproduce it by installing the stored coefficients, not by re-fitting (measured
# 2026-07-23 — the same procedure on the same frames under a different Hugin
# build returns coefficients 3.9%/30.6% apart, so a re-fit is a NEW model, never
# a reproduction of an old one).
#
# The lens and focal are read from the set's own `acquisition.json`
# (`exif.lens`, `exif.focal_length_mm` — exiftool for raws, FITS headers for
# astrocam frames), then the model is looked up in the pinned file. Nothing about
# a particular body is hardcoded here.
#
# `--from-fit` installs a set's `qa_work/lens_fit.json` instead, and says loudly
# that it is NOT the pinned model. That distinction matters: reading the fit
# record by default meant `install_lens_model.sh <session> <set>` silently
# installed whichever fit had last run for that set, so the same command could
# mean two different optical models on two different days.
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
# The marker records `replaced a=… b=… c=…` and NEVER the verbatim
# `<distortion .../>` element: a second parseable copy of a distortion line
# inside the same <lens> block is a DECOY, and every raw-text scanner — the
# idempotence test and the replace target here, and lens_preflight.py's
# installed-vs-pinned assertion — matches the comment's copy
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

LENS= FOCAL= SESSION= SET= FROMFIT=0 REPLACE=0 CENTER= ABC=()
if [ "${1:-}" = "--lens" ] || [ "${1:-}" = "--focal" ]; then
  while [ $# -gt 0 ]; do case "$1" in
    --lens) LENS=$2; shift 2;;
    --focal) FOCAL=$2; shift 2;;
    --from-fit) FROMFIT=1; shift;;
    --replace) REPLACE=1; shift;;
    --center) CENTER=$2; shift 2;;
    *) ABC+=("$1"); shift;;
  esac; done
else
  SESSION=${1:?usage: install_lens_model.sh <session-dir> <set> [--from-fit]  |  --lens M --focal F [a b c]}
  SET=${2:?missing <set>}
  shift 2
  while [ $# -gt 0 ]; do case "$1" in
    --from-fit) FROMFIT=1; shift;;
    --replace) REPLACE=1; shift;;
    --center) CENTER=$2; shift 2;;
    *) ABC+=("$1"); shift;;
  esac; done
fi
[ ${#ABC[@]} -eq 0 ] || [ ${#ABC[@]} -eq 3 ] || {
  echo "install_lens_model: pass all three of a b c, or none (then the fit record supplies them)" >&2; exit 1; }
[ -d "$DBDIR" ] || { echo "install_lens_model: $DBDIR missing — run lensfun-update-data first" >&2; exit 1; }

python3 - "$REPO" "$DBDIR" "${SESSION:-}" "${SET:-}" "$LENS" "$FOCAL" "$FROMFIT" "$REPLACE" "$CENTER" "${ABC[@]}" <<'PY'
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

repo, dbdir, session, sset, lens, focal, fromfit, replace, center = sys.argv[1:10]
abc = sys.argv[10:]
fromfit, replace = fromfit == "1", replace == "1"
if center:
    try:
        cx, cy = (float(v) for v in center.split(","))
    except ValueError:
        sys.exit("install_lens_model: --center takes X,Y in lensfun's normalised "
                 "units (see the <center> note in the header).")
    center = (cx, cy)
PINNED = os.path.join(repo, "scripts", "darktable", "lens_models.json")

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
    if fromfit and not abc:
        fit_p = os.path.join(d, "qa_work", "lens_fit.json")
        try:
            fit = json.load(open(fit_p))["fitted_ptlens"]
        except (OSError, ValueError, KeyError) as e:
            sys.exit(f"install_lens_model: no fitted model at {fit_p} ({e}) — run "
                     "scripts/darktable/fit_lens_model.sh for this set first.")
        abc = [repr(float(fit[k])) for k in ("a", "b", "c")]
        source = f"FRESH FIT from {fit_p} — NOT the pinned model"
if not lens or focal in ("", None):
    sys.exit("install_lens_model: need a lens and a focal (from the set's record, "
             "or --lens/--focal).")

# ---- the PINNED model is the authority when nothing else was named --------
def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

f0 = float(focal)
focal_key = str(int(f0)) if f0 == int(f0) else str(f0)
key = f"{lens}@{focal_key}"
if not abc:
    try:
        pinned = json.load(open(PINNED))
    except (OSError, ValueError) as e:
        sys.exit(f"install_lens_model: cannot read {PINNED} ({e}) — it is the "
                 "authority for what ships, so this STOPS.")
    # match the pinned key the SAME way the DB block is matched: the EXIF string
    # ("NIKKOR Z 24-70mm f/4 S") and lensfun's spelling ("Nikkor Z 24-70mm f/4 S")
    # differ in case, and a model must not be missed over capitalisation.
    entry = next((v for k, v in pinned.items()
                  if not k.startswith("_") and norm(k) == norm(key)), None)
    if entry is None:
        have = [k for k in pinned if not k.startswith("_")]
        sys.exit(f"install_lens_model: no PINNED model for {key!r}.\n"
                 f"  pinned: {have or '(none)'}\n"
                 "  Fit one (scripts/darktable/fit_lens_model.sh <session> <set> ...),\n"
                 "  then add it to scripts/darktable/lens_models.json with its\n"
                 "  provenance. A fresh fit is a CANDIDATE until it is pinned —\n"
                 "  --from-fit installs one without pinning, for an A/B only.")
    pt = entry["ptlens"]
    abc = [repr(float(pt[k])) for k in ("a", "b", "c")]
    source = f"PINNED {key} ({entry.get('status', 'no status recorded')[:60]})"
elif "source" not in dir():
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
# The idempotence test must cover BOTH halves of what this script installs — the
# distortion line AND the distortion-ONLY enforcement. Asking only about the
# line reports "already installed" and exits 0 on a block whose <vignetting> has
# come back while the coefficients stayed right, leaving the DB
# double-correcting: MEASURED by reinstating the fitted lens's focal=70
# aperture=4 vignetting pair by hand — verify_lens_card read a 4219 ADU
# corner-vs-centre step on a 30000 ADU uniform card (tol 1.0) while this script
# said there was nothing to do. That matters more now that lens_preflight
# --require-profile runs the card check every set and names THIS command as the
# fix: advice that no-ops in the state the guard reports is worse than no advice.
n_live = len(re.findall(r"<(?:vignetting|tca)\b", live(block)))
if new_line in live(block) and prior and not center and n_live == 0:
    print(f"install_lens_model: already installed for {db_model} @ {focal_s}mm "
          f"({os.path.basename(path)})")
    sys.exit(0)
if n_live and new_line in live(block) and prior:
    print(f"install_lens_model: coefficients already pinned, but {n_live} live "
          f"<vignetting>/<tca> entr{'y' if n_live == 1 else 'ies'} are back in "
          f"{db_model} — re-stripping (darktable applies its DEFAULT correction "
          f"set, and only this DB chooses otherwise)")
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
    # Record the replaced COEFFICIENTS, never the verbatim element. Embedding
    # the whole `<distortion .../>` tag for self-description creates the decoy
    # that defeats every scanner in this file and in
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

# ---- optional DISTORTION CENTRE ------------------------------------------
# lensfun's <center x= y=/> is a child of <lens> (database.cpp requires the
# "lens" context), so it is PER-LENS, not per-focal: one centre applies to
# every focal in the block. UNITS, from modifier.cpp: the distortion origin is
# Width/2 + CenterX*(size/2) with size = the image HEIGHT, so one unit is half
# the image height (2020 px on this 6064x4040 body), axes in darktable's image
# convention (x right, y DOWN).
# It is absent from lensfun's shipped DTD/XSD but IS parsed (database.cpp) and
# applied (mod-coord.cpp ApplyGeometryDistortion, which subtracts the centre
# before the radial callbacks and adds it back after) in 0.3.4 — verified in
# the installed liblensfun.so.0.3.4, which carries the "center" string.
# WHY OPT-IN: a,b,c are fitted ABOUT a centre. Moving the centre under
# coefficients fitted for centre=0 is a DIFFERENT model, not a refinement of
# the same one, so it is a separately bracketed knob and only a measurement on
# a real product says whether it is better.
center_note = ""
if center:
    cel = f'<center x="{center[0]:g}" y="{center[1]:g}"/>'
    live_c = re.search(r"<center\b[^>]*/>", live(new_block))
    if center == (0.0, 0.0):
        if live_c:
            new_block = new_block[:live_c.start()] + new_block[live_c.end():]
            center_note = "; centre element REMOVED"
    elif live_c and live_c.group(0) == cel:
        center_note = f"; centre {cel} (unchanged)"
    elif live_c:
        if not replace:
            sys.exit(f"install_lens_model: {lens} already carries a DIFFERENT "
                     f"{live_c.group(0)} — pass --replace to swap it, or "
                     "--center 0,0 to remove it.")
        new_block = new_block[:live_c.start()] + cel + new_block[live_c.end():]
        center_note = f"; centre {cel}"
    else:
        new_block = new_block.replace(
            "<calibration>", "    " + cel + "\n        <calibration>", 1)
        center_note = f"; centre {cel}"

# distortion-only enforcement: strip this lens's vignetting/tca
n_strip = len(re.findall(r"<(?:vignetting|tca)\b", new_block))
new_block = re.sub(r"\s*<(?:vignetting|tca)\b[^>]*/>", "", new_block)
if "<distortion" not in live(new_block):
    sys.exit("install_lens_model: the edit would leave no distortion model — refusing.")

marker = (f'<!-- {MARK} focal={focal_s} {what}{center_note}; '
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
if center_note:
    print(f" {center_note.lstrip(';')} — PER-LENS (all focals), units = half the "
          "image height")
print(f"  stripped {n_strip} vignetting/tca entries — distortion-only holds")
print(f"  {path}")
PY
