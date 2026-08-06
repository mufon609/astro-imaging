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
