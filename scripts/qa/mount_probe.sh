#!/usr/bin/env bash
# TWO-WINDOW mount drift probe — the precise instrument of the fingerprint's
# mount cross-check (scripts/lib/fingerprint.py): solve the set's FIRST and
# LAST frames, record both solves + capture epochs, and let the fingerprint
# derive the drift signature (a fixed mount advances RA at the sidereal rate
# with Dec constant; tracked holds both). This is the instrument that can
# decisively measure FIXED — the trail-vs-roundness check is one-sided (round
# stars rule fixed OUT) — and the boundary-regime instrument where roundness
# cannot decide.
#
#   mount_probe.sh <session-dir> <set>
#
# Every pixel op and measurement is a tool's: Siril decodes a camera raw and
# extracts the CFA's green plane (the proven single-frame decode pattern —
# anomaly_audit.py; a FITS light needs no decode and solves as-is);
# astrometry.net solves both windows (solve_field.py, blind); capture epochs
# come from EXIF/DATE-OBS. This script only orchestrates and records:
# datasets/<session>/<set>/qa_work/mount_probe.json holds both solves +
# epochs, fingerprint.derive() auto-loads it on every refresh (the drift
# measurement survives re-derivation from any call site), and the fingerprint
# CLI prints the verdict (exit 2 on declared-vs-measured CONTRADICT).
#
# Solve domain note: on a camera raw the solved image is the EXTRACTED GREEN
# (half the full-res grid), so the recorded drift's px numbers are green-px
# at the solve's own plate scale — self-consistent, and the mount verdict
# rides the RA rate (deg/hr), which is scale-free.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SESSION=${1:?usage: mount_probe.sh <session-dir> <set>}
SET=${2:?missing <set>}
SESSION=$(cd "$SESSION" && pwd)
SNAME=$(basename "$SESSION")
QW=$REPO/datasets/$SNAME/$SET/qa_work
W=$QW/mount_probe
mkdir -p "$W"
say(){ echo "[mount_probe $SET] $*"; }

mapfile -t FRAMES < <(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' -o -iname '*.fit' -o -iname '*.fits' \) \
  | sort)
N=${#FRAMES[@]}
[ "$N" -ge 2 ] || { say "need >=2 frames, found $N"; exit 1; }
FA=${FRAMES[0]}; FB=${FRAMES[$((N-1))]}
say "windows: $(basename "$FA")  ->  $(basename "$FB")  ($N frames spanned)"

# capture epochs + field width (arcmin) from the set's own metadata
META=$(python3 - "$REPO" "$SESSION" "$SET" "$FA" "$FB" <<'PY'
import json, os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "scripts", "lib"))
import acquisition
epochs = []
for f in (sys.argv[4], sys.argv[5]):
    if os.path.splitext(f)[1].lower() in (".fit", ".fits", ".fts"):
        from astropy.io import fits
        from datetime import datetime
        d = fits.getheader(f).get("DATE-OBS")
        epochs.append(datetime.fromisoformat(str(d)).timestamp() if d else None)
    else:
        rows = acquisition.timeline([f])
        epochs.append(rows[0]["epoch"] if rows else None)
if None in epochs:
    sys.exit("no capture epoch on a probe frame (EXIF/DATE-OBS unreadable)")
acq = {}
try:
    acq = json.load(open(os.path.join(sys.argv[1], "datasets",
                                      os.path.basename(sys.argv[2]),
                                      sys.argv[3], "acquisition.json")))
except (OSError, ValueError):
    pass
fov = ((acq.get("exif") or {}).get("fov_deg"))
print(epochs[0]); print(epochs[1])
print(round(fov * 60.0, 1) if fov else "")
PY
)
{ read -r TA; read -r TB; read -r FWA; } <<< "$META" || true
SPAN=$(python3 -c "print(round(abs($TB - $TA), 1))")
say "span: ${SPAN}s | field width: ${FWA:-unknown} arcmin"

# a camera raw decodes via Siril to the CFA's green plane; FITS solves as-is
prep(){ # <frame> <tag> -> echoes the solvable FITS path
  local f=$1 tag=$2
  case "${f,,}" in
    *.fit|*.fits|*.fts) echo "$f"; return;;
  esac
  local stem; stem=$(basename "${f%.*}")
  printf 'requires 1.4.4\nsetcompress 0\nload %s\nextract_Green\nload Green_%s\nsave %s\n' \
    "$f" "$stem" "$W/${tag}_green" > "$W/${tag}.ssf"
  flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$W/${tag}.ssf" \
    > "$W/${tag}_siril.log" 2>&1 || true
  rm -f "$W/Green_${stem}".fit*
  [ -f "$W/${tag}_green.fit" ] || { say "siril decode failed — $W/${tag}_siril.log" >&2; exit 1; }
  echo "$W/${tag}_green.fit"
}
SA_FIT=$(prep "$FA" a)
SB_FIT=$(prep "$FB" b)

solve(){ # <fits> <tag>
  say "solve $2 ($(basename "$1"))"
  python3 "$REPO/scripts/calibrate/solve_field.py" "$1" \
    --json="$W/solve_$2.wcs.json" ${FWA:+--field-width-arcmin=$FWA} \
    > "$W/solve_$2.log" 2>&1 || { tail -3 "$W/solve_$2.log" >&2; exit 1; }
  # the sibling record solve_field writes beside the input carries ra/dec/scale
}
solve "$SA_FIT" a
solve "$SB_FIT" b

python3 - "$REPO" "$SNAME" "$SET" "$W" "$SA_FIT" "$SB_FIT" "$FA" "$FB" "$TA" "$TB" <<'PY'
import json, math, os, sys
repo, sname, sset, w, sa, sb, fa, fb, ta, tb = sys.argv[1:11]
from astropy.io import fits
from astropy.wcs import WCS

out = {}
for tag, solved, frame, t in (("a", sa, fa, float(ta)), ("b", sb, fb, float(tb))):
    # the --json record is the solver's WCS header ({KEY: [value, comment]});
    # evaluate it at the frame CENTER pixel — CRVAL alone is tied to the
    # solver's arbitrary CRPIX and cannot be compared between two solves
    hdr = {k: v[0] for k, v in
           json.load(open(os.path.join(w, f"solve_{tag}.wcs.json"))).items()}
    h = fits.getheader(solved)
    wcs = WCS(hdr)
    sky = wcs.pixel_to_world(h["NAXIS1"] / 2.0, h["NAXIS2"] / 2.0)
    det = abs(hdr["CD1_1"] * hdr["CD2_2"] - hdr["CD1_2"] * hdr["CD2_1"])
    out[f"solve_{tag}"] = {"frame": os.path.basename(frame), "time_s": t,
                           "ra_deg": round(float(sky.ra.deg), 6),
                           "dec_deg": round(float(sky.dec.deg), 6),
                           "scale_arcsec_px": round(3600.0 * math.sqrt(det), 4)}
rec = {"tool": ("Siril decode/extract_Green (camera raw) + astrometry.net "
                "blind solves (solve_field.py --json WCS, evaluated at the "
                "frame-center pixel via astropy); epochs from EXIF/DATE-OBS; "
                "consumed by scripts/lib/fingerprint.py (auto-loaded on "
                "every refresh — the drift measurement is durable)"),
       "domain_note": ("camera-raw solves run on the extracted GREEN plane "
                       "(half-res grid): px figures are green-px at the "
                       "solve's own scale; the mount verdict rides the "
                       "scale-free RA rate"),
       **out}
p = os.path.join(repo, "datasets", sname, sset, "qa_work", "mount_probe.json")
json.dump(rec, open(p, "w"), indent=1)
print(f"[mount_probe {sset}] record -> {p}")
PY

rm -f "$W"/*_green.fit "$W"/*.ssf
# the fingerprint consumes the probe record and prints the verdict; exit 2
# (declared-vs-measured CONTRADICT) propagates to the caller
python3 "$REPO/scripts/lib/fingerprint.py" "$SESSION" "$SET"
