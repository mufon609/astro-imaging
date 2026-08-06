#!/usr/bin/env bash
# F212N at-source striping arm: Detector1 on the 12 SW ramps with
# clean_flicker_noise ENABLED, then Image2 and the grouped-default stage 3.
# One knob vs the default rebuild (jup_f212n_rebuilt_i2d): the cfn step.
# Anti-trap configuration (researched from the installed step spec; the
# skymatch glow-absorption dead-end is the cautionary mechanism):
#   background_method='model' + box 256 — a low-res Background2D absorbs the
#   planet's smooth glow into the PROTECTED background (removed before the
#   noise fit, restored after), so glow cannot leak into the correction;
#   fit_by_channel=True — NIRCam 1/f is per-amplifier;
#   save_mask/save_background — verification surfaces (mask must cover the
#   disc; the model must follow the glow), checked before the verdict.
# ramp_fit stays default (F212N has no one-group crescent problem).
# Idempotent: legs skip when their outputs exist.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
L2="$REPO/sessions/jwst-jupiter/work/l2"
PROD="$REPO/sessions/jwst-jupiter/products"
VBIN="$HOME/.local/share/jwst-pipe-venv/bin"
export CRDS_PATH="$HOME/.local/share/crds_cache"
export CRDS_SERVER_URL="https://jwst-crds.stsci.edu"
export PYTHONUNBUFFERED=1
echo "jwst + CRDS context for this arm:"
"$VBIN/python3" -c "import jwst, crds; print('jwst', jwst.__version__, '| context', crds.get_default_context())"
mkdir -p "$L2/cfn"; cd "$L2/cfn"

echo "=== [1/3] Detector1 + clean_flicker_noise on 12 SW ramps ==="
for u in "$PROD"/jw01373008001_03101_0000{1,2,3}_nrcb{1,2,3,4}_uncal.fits; do
    base="$(basename "$u" _uncal.fits)"
    if [ -f "${base}_rate.fits" ]; then echo "skip ${base}"; continue; fi
    "$VBIN/strun" calwebb_detector1 "$u" \
        --steps.clean_flicker_noise.skip=False \
        --steps.clean_flicker_noise.background_method=model \
        --steps.clean_flicker_noise.background_box_size=256,256 \
        --steps.clean_flicker_noise.fit_by_channel=True \
        --steps.clean_flicker_noise.save_mask=True \
        --steps.clean_flicker_noise.save_background=True \
        --output_dir=.
done

echo "=== [2/3] Image2 ==="
for r in jw01373008001_03101_0000?_nrcb?_rate.fits; do
    base="${r%_rate.fits}"
    if [ -f "${base}_cal.fits" ]; then echo "skip ${base}"; continue; fi
    "$VBIN/strun" calwebb_image2 "$r" --steps.resample.skip=True --output_dir=.
done

echo "=== [3/3] Stage 3 (grouped default skymatch) ==="
if [ ! -f jup_f212n_rebuilt_cfn_i2d.fits ]; then
    "$VBIN/asn_from_list" -o f212n_cfn_asn.json --product-name jup_f212n_rebuilt_cfn \
        -r DMS_Level3_Base jw01373008001_03101_0000?_nrcb?_cal.fits
    "$VBIN/strun" calwebb_image3 f212n_cfn_asn.json \
        --steps.tweakreg.skip=True --steps.source_catalog.skip=True \
        --steps.outlier_detection.in_memory=False --output_dir=.
else echo "skip stage3 (i2d exists)"; fi

echo "=== CFN ARM COMPLETE ==="
ls -la jup_f212n_rebuilt_cfn_i2d.fits
