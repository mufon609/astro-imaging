#!/usr/bin/env bash
# Install a MEASURED distortion model into the live lensfun user DB (the one
# darktable reads), for the lens and focal a given SET was actually shot with.
#
#   install_lens_model.sh <session-dir> <set>            install the PINNED model
#   install_lens_model.sh --lens "<model>" --focal <mm>   same, named explicitly
#   install_lens_model.sh <session-dir> <set> --from-fit  install that set's FRESH fit
#   install_lens_model.sh --lens M --focal F a b c        explicit coefficients
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
# SAFETY: the edit records what it replaced in an XML comment inside the block,
# so the patch is self-describing and reversible, and a block already carrying a
# marker with DIFFERENT coefficients STOPS rather than being silently
# overwritten — a re-fit is an explicit act. (Comments inside <lens> are known
# safe: upstream ships them, e.g. "<!-- Taken with Nikon Z6 -->".)
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

LENS= FOCAL= SESSION= SET= FROMFIT=0 ABC=()
if [ "${1:-}" = "--lens" ] || [ "${1:-}" = "--focal" ]; then
  while [ $# -gt 0 ]; do case "$1" in
    --lens) LENS=$2; shift 2;;
    --focal) FOCAL=$2; shift 2;;
    --from-fit) FROMFIT=1; shift;;
    *) ABC+=("$1"); shift;;
  esac; done
else
  SESSION=${1:?usage: install_lens_model.sh <session-dir> <set> [--from-fit]  |  --lens M --focal F [a b c]}
  SET=${2:?missing <set>}
  shift 2
  while [ $# -gt 0 ]; do case "$1" in
    --from-fit) FROMFIT=1; shift;;
    *) ABC+=("$1"); shift;;
  esac; done
fi
[ ${#ABC[@]} -eq 0 ] || [ ${#ABC[@]} -eq 3 ] || {
  echo "install_lens_model: pass all three of a b c, or none (then the fit record supplies them)" >&2; exit 1; }
[ -d "$DBDIR" ] || { echo "install_lens_model: $DBDIR missing — run lensfun-update-data first" >&2; exit 1; }

python3 - "$REPO" "$DBDIR" "${SESSION:-}" "${SET:-}" "$LENS" "$FOCAL" "$FROMFIT" "${ABC[@]}" <<'PY'
import glob, json, os, re, sys
from datetime import date

repo, dbdir, session, sset, lens, focal, fromfit = sys.argv[1:8]
abc = sys.argv[8:]
fromfit = fromfit == "1"
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
if new_line in block and prior:
    print(f"install_lens_model: already installed for {db_model} @ {focal_s}mm "
          f"({os.path.basename(path)})")
    sys.exit(0)
if prior and new_line not in block:
    sys.exit(f"install_lens_model: {db_model} @ {focal_s}mm already carries a "
             f"DIFFERENT fitted entry ({prior.group(1).strip()}). A re-fit is an "
             "explicit act: remove that line (or re-run lensfun-update-data to "
             "reset the DB) before installing another.")

existing = re.search(rf'<distortion[^>]*focal="{re.escape(focal_s)}"[^>]*/>', block)
if existing:
    new_block = block.replace(existing.group(0), new_line)
    what = f"replaced {existing.group(0)}"
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
if "<distortion" not in new_block:
    sys.exit("install_lens_model: the edit would leave no distortion model — refusing.")

marker = (f'<!-- {MARK} focal={focal_s} {what}; '
          f'{"from " + os.path.basename(os.path.abspath(session)) + "/" + sset + "; " if session else ""}'
          f'vignetting+tca stripped ({n_strip}); {date.today().isoformat()} -->')
new_block = new_block.replace("<calibration>", marker + "\n        <calibration>", 1)

open(path, "w", encoding="utf-8").write(xml.replace(block, new_block))
print(f"install_lens_model: {db_model} @ {focal_s}mm — {what}")
print(f"  source: {source}")
print(f"  a={a} b={b} c={c}")
print(f"  stripped {n_strip} vignetting/tca entries — distortion-only holds")
print(f"  {path}")
PY
