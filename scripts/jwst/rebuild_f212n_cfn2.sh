#!/usr/bin/env bash
# cfn arm 2: identical to arm 1 except the ONE knob — an explicit per-exposure
# user_mask (True=background, source-verified) built as finite AND
# rate < 1.5 MJy/sr, 15-px dilated exclusion (sessions/.../l2/masks/), so the
# planet disc+glow can never enter the background/noise fits. Everything else
# carries from arm 1 (background model box 256, per-channel fit).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
L2="$REPO/sessions/jwst-jupiter/work/l2"
PROD="$REPO/sessions/jwst-jupiter/products"
VBIN="$HOME/.local/share/jwst-pipe-venv/bin"
export CRDS_PATH="$HOME/.local/share/crds_cache"
export CRDS_SERVER_URL="https://jwst-crds.stsci.edu"
export PYTHONUNBUFFERED=1
mkdir -p "$L2/cfn2"; cd "$L2/cfn2"
for u in "$PROD"/jw01373008001_03101_0000{1,2,3}_nrcb{1,2,3,4}_uncal.fits; do
    base="$(basename "$u" _uncal.fits)"
    if [ -f "${base}_rate.fits" ]; then echo "skip ${base}"; continue; fi
    "$VBIN/strun" calwebb_detector1 "$u" \
        --steps.clean_flicker_noise.skip=False \
        --steps.clean_flicker_noise.background_method=model \
        --steps.clean_flicker_noise.background_box_size=256,256 \
        --steps.clean_flicker_noise.fit_by_channel=True \
        --steps.clean_flicker_noise.user_mask="$L2/masks/${base}_skymask.fits" \
        --output_dir=.
done
for r in jw01373008001_03101_0000?_nrcb?_rate.fits; do
    base="${r%_rate.fits}"
    if [ -f "${base}_cal.fits" ]; then echo "skip ${base}"; continue; fi
    "$VBIN/strun" calwebb_image2 "$r" --steps.resample.skip=True --output_dir=.
done
if [ ! -f jup_f212n_rebuilt_cfn2_i2d.fits ]; then
    "$VBIN/asn_from_list" -o f212n_cfn2_asn.json --product-name jup_f212n_rebuilt_cfn2 \
        -r DMS_Level3_Base jw01373008001_03101_0000?_nrcb?_cal.fits
    "$VBIN/strun" calwebb_image3 f212n_cfn2_asn.json \
        --steps.tweakreg.skip=True --steps.source_catalog.skip=True \
        --steps.outlier_detection.in_memory=False --output_dir=.
fi
rm -f jw*_rateints.fits
echo "=== CFN2 ARM COMPLETE ==="
ls -la jup_f212n_rebuilt_cfn2_i2d.fits
