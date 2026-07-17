#!/usr/bin/env bash
# Single source of truth for the light-frame calibration command, shared by
# every stack builder (run_pipeline.sh, run_undistort_pipeline.sh, and the
# lights.ssf template via @CALIBRATE@). Dark subtraction and -cc=dark cosmetic
# hot/cold-pixel correction are the INVARIANT core of light calibration and are
# injected here, so no builder can emit a light calibrate without them. The
# CFA / flat / debayer flags vary per path (a dual-band set calibrates the CFA
# mosaic without debayering; the undistort path equalizes the CFA before
# debayer) and are passed by the caller.
#
# -cc=dark 3 3 is mandatory: it replaces the master dark's hot/cold pixels from
# its bad-pixel map. Left uncorrected, those fixed-sensor-position pixels are
# dragged into streaks along the drift of an un-dithered stack (walking noise).
# A separate, hand-written calibrate line in one builder once omitted it and
# shipped that defect; routing every path through this one function is what
# prevents a documented flag from living in one builder and missing in another.
# scripts/stack/check_calibrate.sh enforces that no path bypasses it.
#
#   calibrate_light_cmd <seq> <dark> [extra Siril `calibrate` flags...]
# e.g.
#   calibrate_light_cmd light masters/dark_master -flat=masters/flat_master -equalize_cfa -cfa -debayer
#   calibrate_light_cmd c "$DARK" -flat="$FLAT" -equalize_cfa -cfa -debayer -prefix=pp_
calibrate_light_cmd() {
  local seq=$1 dark=$2
  shift 2
  echo "calibrate $seq -dark=$dark -cc=dark 3 3 $*"
}
