#!/usr/bin/env bash
# Rebuild the jwst-jupiter wide-field filters from level 2 with the OFFICIAL
# jwst pipeline, under our recorded control — the at-source fix for the L3
# defects measured on the archive products:
#   - F335M saturation crescents: the limb saturates after ramp group 1 and
#     the pipeline default suppress_one_group=True discards one-group slopes
#     (-> NaN). Detector1 re-runs on the _uncal ramps with recovery ENABLED,
#     then Image2 makes our own _cal set.
#   - Sky detector-block steps + outlier specks (both filters): our own
#     stage 3 (skymatch + outlier_detection + resample) replaces the archive
#     combine; F212N uses the archive _cal files (its ramps need no recovery
#     — the L3 disc is hole-free, measured).
# Moving target: calwebb_image3 runs assign_mtwcs for TARGTYPE=moving data
# (verify in the log); tweakreg and source_catalog are skipped (no star grid
# to align on a planet field; catalog unused).
# CRDS runs at the CURRENT operational context (resolved + logged at start):
# the code (jwst 3.0.0) and context must be a coherent pair — pinning the
# archive's 2022-era context under current code broke Image2 on an unknown
# reference type (chromcorr); the recorded anchors for OUR products are the
# code+context pair this log captures.
# Idempotent: every leg skips if its output exists — safe to re-run/resume.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
L2="$REPO/sessions/jwst-jupiter/work/l2"
PROD="$REPO/sessions/jwst-jupiter/products"
VBIN="$HOME/.local/share/jwst-pipe-venv/bin"
export CRDS_PATH="$HOME/.local/share/crds_cache"
export CRDS_SERVER_URL="https://jwst-crds.stsci.edu"
export PYTHONUNBUFFERED=1
echo "jwst + CRDS context for this rebuild:"
"$VBIN/python3" -c "import jwst, crds; print('jwst', jwst.__version__, '| context', crds.get_default_context())"
mkdir -p "$L2"; cd "$L2"

echo "=== [1/4] Detector1: F335M ramps, one-group recovery ON ==="
for u in "$PROD"/jw01373008001_03101_0000{1,2,3}_nrcblong_uncal.fits; do
    base="$(basename "$u" _uncal.fits)"
    if [ -f "${base}_rate.fits" ]; then echo "skip ${base} (rate exists)"; continue; fi
    "$VBIN/strun" calwebb_detector1 "$u" \
        --steps.ramp_fit.suppress_one_group=False --output_dir=.
done

echo "=== [2/4] Image2: recovered rates -> our cal set ==="
for r in jw01373008001_03101_0000?_nrcblong_rate.fits; do
    base="${r%_rate.fits}"
    if [ -f "${base}_cal.fits" ]; then echo "skip ${base} (cal exists)"; continue; fi
    "$VBIN/strun" calwebb_image2 "$r" --steps.resample.skip=True --output_dir=.
done

echo "=== [3/4] Stage 3: F335M (our recovered cal x3) ==="
if [ ! -f jup_f335m_rebuilt_i2d.fits ]; then
    "$VBIN/asn_from_list" -o f335m_asn.json --product-name jup_f335m_rebuilt \
        -r DMS_Level3_Base jw01373008001_03101_0000?_nrcblong_cal.fits
    "$VBIN/strun" calwebb_image3 f335m_asn.json \
        --steps.tweakreg.skip=True --steps.source_catalog.skip=True \
        --steps.outlier_detection.in_memory=False --output_dir=.
else echo "skip f335m stage3 (i2d exists)"; fi

echo "=== [4/4] Stage 3: F212N (archive cal x12) ==="
if [ ! -f jup_f212n_rebuilt_i2d.fits ]; then
    "$VBIN/asn_from_list" -o f212n_asn.json --product-name jup_f212n_rebuilt \
        -r DMS_Level3_Base "$PROD"/jw01373008001_03101_0000?_nrcb[1-4]_cal.fits
    "$VBIN/strun" calwebb_image3 f212n_asn.json \
        --steps.tweakreg.skip=True --steps.source_catalog.skip=True \
        --steps.outlier_detection.in_memory=False --output_dir=.
else echo "skip f212n stage3 (i2d exists)"; fi

echo "=== REBUILD COMPLETE ==="
ls -la jup_f335m_rebuilt_i2d.fits jup_f212n_rebuilt_i2d.fits
