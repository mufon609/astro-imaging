#!/usr/bin/env bash
# One-knob A/B on the lensfun <center> element: warp ONE frame through the
# production darktable invocation and measure the residual distortion field.
# Usage: warp_ab.sh <arm-tag>
set -euo pipefail
REPO=/home/samsung/Desktop/astro-imaging
W=$REPO/datasets/aug06/set-01/disto_work
ARM=${1:?usage: warp_ab.sh <arm-tag>}
CFG=$W/dtcfg
SRC=$REPO/sessions/aug06/set-01/DSC_6488.NEF

mkdir -p "$W/tif"
# 1. raw -> FITS (Siril convert -debayer), same as the shape-gradient probe
if [ ! -f "$W/lt_00001.fit" ]; then
  cp "$SRC" "$W/" 2>/dev/null || true
  flatpak run --command=siril-cli org.siril.Siril -d "$W" -s "$W/convert.ssf" >/dev/null 2>&1
fi
# 2. FITS -> 32-bit float TIFF
printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\nload %s\nsavetif32 %s\n' \
  "$W/lt_00001.fit" "$W/tif/in" > "$W/tif.ssf"
flatpak run --command=siril-cli org.siril.Siril -d "$W/tif" -s "$W/tif.ssf" >/dev/null 2>&1
# 3. EXIF for the lens match + strip ICC (the production float-leg contract)
exiftool -q -overwrite_original -TagsFromFile "$SRC" -Make -Model -LensModel \
  -FocalLength -FNumber -icc_profile:all= "$W/tif/in.tif"
# 4. the production warp, verbatim
[ -d "$CFG" ] || "$REPO/scripts/darktable/install_styles.sh" "$CFG" >/dev/null 2>&1
rm -f "$W/tif/w_$ARM.tif"
timeout 900 darktable-cli "$W/tif/in.tif" "$W/tif/w_$ARM.tif" \
  --style lensdist --style-overwrite --icc-type LIN_REC709 --core \
  --configdir "$CFG" --library ":memory:" \
  --conf plugins/imageio/format/tiff/bpp=32 \
  --conf plugins/imageio/format/tiff/compress=0 > "$W/dt_$ARM.log" 2>&1
grep -iE "lens correction|lensfun|autoscale" "$W/dt_$ARM.log" | head -3 || true
# 5. warped TIFF -> FITS for the probe
printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nload w_%s.tif\nsave wf_%s\n' \
  "$W/tif" "$ARM" "$ARM" > "$W/back.ssf"
flatpak run --command=siril-cli org.siril.Siril -d "$W/tif" -s "$W/back.ssf" >/dev/null 2>&1
ls -la "$W/tif/w_$ARM.tif" "$W/tif/wf_$ARM.fit"
md5sum "$W/tif/in.tif" "$W/tif/w_$ARM.tif"
