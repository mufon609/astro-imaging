#!/usr/bin/env bash
# Stack builder for the wide-field UNTRACKED class: calibrate -> UNDISTORT ->
# register -> stack. A far-drifting set cannot be registered by one homography
# (the real frame-to-frame map is distort . H . distort^-1), so the lens
# distortion is removed BEFORE registration by darktable + the lensfun model
# this rig carries (community DB entry, or the entry fitted from the set's own
# frames via scripts/darktable/fit_lens_model.sh + install_lens_model.sh where
# the community profile is inadequate — docs/wide-field-untracked-registration.md).
#
#   run_undistort_pipeline.sh <session-dir> <set> --dark=<master> --flat=<master> \
#                             [--frames=N | --select=<list-file>] [--chunk=12] [--out=<stack.fit>]
#                             [--regdata=<lt_.seq>] [--nonorm] [--keep-out]
#
# --select=<file> (one raw path per line) processes exactly those frames in
# order — the group-composition driver (run_undistort_groups.sh) uses it to
# feed consecutive blocks; mutually exclusive with --frames.
#
# THE TWO A/B FLAGS (diagnostic; the default path is untouched by both). A
# controlled A/B on this route moves ONE knob — the calibration — and everything
# downstream of it must then be held fixed by construction, not by hope:
#
# --regdata=<file>  PIN THE REGISTRATION (the TRANSFORMS half). Absent, each
#     arm runs its own `register -2pass`, whose star lists — and so its
#     homographies — move with the calibration. Before the reference pin below
#     the 2pass's FIRST pass also re-chose the reference frame from image
#     quality, and the calibration changed that choice: MEASURED here, 12
#     frames of aug09/set-05, one knob (the flat): with `skyflat_set-05` the
#     2pass chose image 1 and delivered a 4896x3616 canvas; with
#     `skyflat_set-01` it chose image 2 and delivered 4887x3641. Two arms whose
#     canvases differ are not pixel-comparable at all, and the difference is a
#     SECOND knob nobody asked for. With this flag the first arm writes its
#     `lt_.seq` (Siril's own registration data: the per-image homographies and
#     the reference index) to <file>, and every later arm is handed that same
#     file and does not re-register. The transforms are then bit-identical
#     across arms, so the ONLY difference in the products is the calibration.
#     Both arms estimate the SAME geometric truth — the frames, the lens model
#     and the warp are identical — so sharing one estimate removes a nuisance
#     difference rather than introducing one.
#     (The REFERENCE half of that lottery is closed on this route: `setref lt 1`
#     after the 2pass, the groups route's own pin, time order — the production
#     path only; a donor lt_.seq carries the donor's reference verbatim and is
#     never re-pinned. the -output_norm zero-point entry in docs/dead-ends/stacking-compose.md.)
# --nonorm  stack with `-nonorm` instead of `-norm=addscale`.
#     DIAGNOSTIC ONLY, never a deliverable: the per-frame normalization
#     coefficients are computed from the frames' OWN statistics, so on a
#     calibration A/B they are computed from data that differs BETWEEN the arms
#     and partially absorb the very difference under test. Run the arms at
#     `-nonorm` to see the unabsorbed difference, and the same pair at the
#     production clause to MEASURE the absorption. The flag stamps
#     STACKNRM='nonorm' on the product so a diagnostic stack cannot be mistaken
#     for a shipped one later.
# --keep-out  DIAGNOSTIC: keep $P/out (the lt_ frames, the r_lt_ registered
#     copies and both .seq files, ~55 GB for a 100-frame group) instead of
#     deleting it after the stack — the only way to attribute a clamped or
#     zeroed pixel of the sub-stack to the frames that made it. Delete by hand.
#
# Ordering is load-bearing: darks/flats are sensor-grid properties, so
# calibration finishes in SENSOR space, debayer follows (a CFA mosaic cannot be
# interpolated), and only then the geometric warp.
#
# GUARDS, in order:
# - scripts/stack/lens_preflight.py --require-profile: STOPS on a mixed-optics
#   set and makes darktable PROVE it corrects this set — darktable applies NO
#   correction to a lens lensfun cannot match, silently (exit 0, empty log).
# - chunk remainder: Siril cannot build a sequence from ONE frame, so a frame
#   count leaving a remainder of exactly 1 auto-shrinks the chunk by one and
#   states it (chunk size only bounds working-set residency, so it is free) —
#   the same recovery run_frame_qa.sh makes for its batches.
# - disk: registration keeps the warped input set resident while seqapplyreg
#   writes the registered set beside it, so the peak is the SUM of two frames.
#   `undistort_peak_gib` (scripts/stack/disk_budget.sh) DERIVES it from this
#   set's own frame geometry — W x H x channels x 4 bytes x 2 — rather than a
#   per-camera constant, and is SHARED with run_set_chain.sh's routing decision
#   (the two were separate constants once and diverged by 2x). NOTHING in the pipeline is
#   compressed, the pipeline-wide rule; every .ssf pins `setcompress 0`. Aborts
#   up front if the selected frame count cannot fit; --frames=N selects an EVEN
#   STRIDE over the whole set, which preserves the TIME SPAN (what the
#   registration geometry depends on) and trades depth.
#
# BIT DEPTH: 32-bit float end-to-end (set32bits + savetif32 + darktable
# bpp=32). The 16-bit intermediates were an arm-rig RAM/disk adaptation whose
# removal condition fired on the x86 rig — and 16-bit integer quantization was
# a MEASURED defect: a stack's ultra-tight channel histogram quantized to
# MAD=0, degenerating Siril's autostretch statistics (docs/dead-ends.md).
#
#
# The stack rejection is doctrine-selected by sub count (stack_rejection.sh:
# percentile / winsorized / GESD — a deep stack gets GESD), with
# `-norm=addscale` and NO `-output_norm` (a global min-max rescale keyed to one
# darkest pixel; the sub-stack's level is its pinned reference frame's own sky,
# stamped as ANCLOC*/ANCSCL* — the zero-point entry, docs/dead-ends/stacking-compose.md).
# ICC on the FLOAT leg: the TIFF ships UNTAGGED (exiftool strips the profile
# in the same pass that copies the lens EXIF) and darktable exports
# --icc-type LIN_REC709 — measured a PERFECT identity round trip (ratio
# 1.0000 at every level, every channel) with the warp confirmed firing
# (corner 0.22 vs centre 0.003). The former SRGB/SRGB tag-matching contract
# (the 16-bit-era rule) carries a TRC toe-segment mismatch that inflates
# 3s-class sky levels +2..5% below linear ~0.003 (the ICC-toe probe;
# docs/dead-ends.md ICC entry). NEVER use siril `icc_remove` for the strip —
# measured applying a global ~1/12.92 scale through the same leg.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
source "$REPO/scripts/lib/siril_run.sh"   # serialized siril-cli invoker
source "$REPO/scripts/stack/calibrate_light.sh"   # shared light-calibration command (mandatory -cc=dark)
source "$REPO/scripts/stack/stack_rejection.sh"   # shared integration rejection (doctrine-driven by sub count)
source "$REPO/scripts/stack/disk_budget.sh"       # per-set disk peak — shared with the ROUTER, or they drift
source "$REPO/scripts/stack/stamp_headers.sh"     # shared restore of the acquisition keys the warp's TIFF hop drops
SESSION=${1:?usage: run_undistort_pipeline.sh <session-dir> <set> --dark= --flat= [--frames=N] [--chunk=12] [--out=] [--subsky-lights]}
SET=${2:?missing <set>}
DARK= FLAT= FRAMES=0 CHUNK=12 OUT= SELECT= SUBSKYL=0 REGDATA= NONORM=0 KEEPOUT=0
for a in "${@:3}"; do case "$a" in
  --dark=*) DARK=${a#*=};; --flat=*) FLAT=${a#*=};; --frames=*) FRAMES=${a#*=};;
  --chunk=*) CHUNK=${a#*=};; --out=*) OUT=${a#*=};; --select=*) SELECT=${a#*=};;
  --regdata=*) REGDATA=${a#*=};; --nonorm) NONORM=1;; --keep-out) KEEPOUT=1;;
  --subsky-lights) SUBSKYL=1;;
  *) echo "unknown arg $a" >&2; exit 1;;
esac; done
# --subsky-lights: per-frame `subsky 1 -nodither` on each CALIBRATED,
# DEBAYERED light, before the geometric warp — the member background-matching
# step (Siril doctrine: a single frame's gradient is ~degree-1; remove it per
# frame when it varies across the sequence). Default OFF pending the
# BACKLOG:`render-ladder` L1 arm verdict (pre-registered:
# datasets/aug06/experiments.jsonl, `subsky_lights_restoration`).
#
# THE SPLIT IS LOAD-BEARING — this is the UNCOUPLED GOOD HALF of the reverted
# `--desky`, and the two halves must never share a flag again:
# - flat-side half (build_sky_flat --desky, seqsubsky on RAW source frames):
#   a DOMAIN ERROR — background extraction is defined on flat-fielded data —
#   and a measured 31x corner-spread regression. DEAD (docs/dead-ends.md);
#   build_sky_flat.sh keeps it only to reproduce the regressed configuration.
# - lights-side half (THIS flag): the operator's correct domain. A normal sky
#   flat converges to S_mean x V, so calibration leaves each light at about
#   (S_t + O)/S_mean — the per-frame ADDITIVE deviation (S_t - S_mean)/S_mean
#   is what this removes: the member-to-member residual a cross-set compose
#   otherwise carries into its full-coverage corners (measured ~+1%, absent
#   from the min-framed control — the combine-corner audit record). What it
#   does NOT fix: the multiplicative sky x V object tilt (open defect) and
#   real sky structure (which must stay).
# Degree 1 because the MW band IS frame-scale curvature at this focal length
# and degree >= 2 erases it; per-frame rather than composite-level because a
# composite-level plane structurally cannot fit a corner-local term (measured,
# the july23 subsky-on-combine probe) and stack-level-only is reported to
# leave ringing (registry). Runs on DEBAYERED frames, so no CFA caveat.
# `-nodither` is REQUIRED: `seqsubsky` dithers by DEFAULT (unlike `subsky`,
# where -dither is opt-IN) and the dither is UNSEEDED. MEASURED (Siril
# isub+stat, two frames, four runs): identical calibrated input, two default
# runs differ by sigma 0.4 ADU (+-1.0) where two -nodither runs are
# bit-identical; the dither's purpose (quantization terracing) cannot occur
# here — the frames' own bgnoise is 17.7 ADU against the 0.5 ADU step, 35x.
SUBSKYCMD= LPREFIX=pp_
if [ "$SUBSKYL" = 1 ]; then
  SUBSKYCMD='seqsubsky pp_c 1 -nodither\n'; LPREFIX=bkg_pp_
fi
[ -z "$SELECT" ] || [ "$FRAMES" -eq 0 ] || { echo "--select and --frames are mutually exclusive" >&2; exit 1; }
[ -n "$DARK" ] && [ -n "$FLAT" ] || { echo "need --dark= --flat= (matched masters)" >&2; exit 1; }
# Absolutize the masters too: they are embedded into the calibrate .ssf, and
# the flatpak Siril resolves them from the SCRIPT's CWD (work/undistort_*),
# so a caller-relative path fails with "…[any_allowed_extension] not found".
[ -f "$DARK" ] || { echo "no such dark: $DARK" >&2; exit 1; }
[ -f "$FLAT" ] || { echo "no such flat: $FLAT" >&2; exit 1; }
DARK="$(cd "$(dirname "$DARK")" && pwd)/$(basename "$DARK")"
FLAT="$(cd "$(dirname "$FLAT")" && pwd)/$(basename "$FLAT")"
SESSION=$(cd "$SESSION" && pwd)
OUT=${OUT:-$REPO/web/results/$(basename "$SESSION")/stack_$SET}
OUT=${OUT%.fit}
mkdir -p "$(dirname "$OUT")" "$SESSION/work"
# Absolutize: the flatpak Siril sandbox resolves the .ssf's -out= from the
# script's own CWD, so a relative --out lands the final INSIDE the work tree
# and the existence check fails on a stack that actually built.
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
P=$SESSION/work/undistort_$SET
CFG=$SESSION/work/dtcfg
# Outside $P deliberately: $P is wiped per invocation, and the group driver
# invokes this script once per group — the capture must outlive that churn so
# the composing driver can stamp the final from it too.
ACQHDR=$SESSION/work/acq_header_$SET.json
sir(){ siril_run_logged "$P" "$1" "$P/siril.log"; }

LPJ=$REPO/datasets/$(basename "$SESSION")/$SET/qa_work/lens_preflight.json
mkdir -p "$(dirname "$LPJ")"
# BOUND THE LENSFUN-DB LIFECYCLE. The user DB is GLOBAL, unscoped, single-valued
# machine state that nothing reverts — it holds whichever model was installed
# last, indefinitely. run_set_chain.sh installs before calling here, but this
# builder is also invoked DIRECTLY (and by run_undistort_groups.sh), so
# VERIFYING alone is not enough: a direct call warps on whatever the machine
# happens to be carrying, and the preflight stops it — correct, but only after
# the operator has already committed to the run.
# So install the PINNED model first. No --replace: a DIFFERENT fitted entry in
# the DB is an A/B someone staged deliberately, and this builder must not undo it
# silently — the preflight stops on the mismatch and says so.
"$REPO/scripts/darktable/install_lens_model.sh" "$SESSION" "$SET"
python3 "$REPO/scripts/stack/lens_preflight.py" "$SESSION" "$SET" --require-profile --json="$LPJ"
"$REPO/scripts/darktable/install_styles.sh" "$CFG"

mapfile -t SRC < <(find "$SESSION/$SET" -maxdepth 1 -type f \
  \( -iname '*.nef' -o -iname '*.dng' -o -iname '*.cr2' -o -iname '*.cr3' \
     -o -iname '*.arw' -o -iname '*.raf' \) | sort)
# A FITS set reaches here with SRC empty. "no raw frames" is true and points at
# a staging mistake that did not happen — this route's first stage is
# darktable's lens correction, and darktable reads camera raws, not FITS.
[ ${#SRC[@]} -ge 2 ] || {
  nf=$(find "$SESSION/$SET" -maxdepth 1 -type f \( -iname '*.fit' -o -iname '*.fits' \) | wc -l)
  if [ "$nf" -gt 0 ]; then
    echo "ABORT: $SESSION/$SET holds $nf FITS frames and no camera raws. This route" >&2
    echo "  undistorts with darktable, which reads raws — a FITS (dedicated-astrocam)" >&2
    echo "  set cannot take it. Nothing is staged wrong; the route does not accept" >&2
    echo "  this frame format. Use scripts/stack/run_pipeline.sh for the standard" >&2
    echo "  route, or add a FITS path around the darktable stage (a BUILDER change)." >&2
  else
    echo "ABORT: no camera raws (*.nef/dng/cr2/cr3/arw/raf) and no FITS under $SESSION/$SET" >&2
  fi
  exit 1; }
# The ratified per-set cull: recipe.json stack.exclude names frames by their
# trailing FILENAME digits — resolved by the single-source cullspec (loud
# ABORT on an exclude that matches zero or several frames; a cull must never
# silently no-op — a measured trap).
RECIPE=$REPO/datasets/$(basename "$SESSION")/$SET/recipe.json
mapfile -t SRC < <(python3 "$REPO/scripts/lib/cullspec.py" keep "$RECIPE" "${SRC[@]}")
[ ${#SRC[@]} -ge 1 ] || { echo "ABORT: cull resolution failed or left no frames (see cullspec message above)" >&2; exit 1; }
if [ -n "$SELECT" ]; then
  mapfile -t SRC < <(grep -v '^\s*$' "$SELECT")
  for f in "${SRC[@]}"; do [ -f "$f" ] || { echo "ABORT: --select names missing frame $f" >&2; exit 1; }; done
  FRAMES=${#SRC[@]}
fi
[ "$FRAMES" -gt 0 ] || FRAMES=${#SRC[@]}
# A final chunk of exactly ONE frame cannot be sequenced by Siril. Shrink the
# chunk until the remainder is not 1, and say so — aborting here instead was a
# dead end on the one-click chain, which calls this builder WITHOUT a --chunk and
# so had no way to satisfy a demand to "adjust --chunk": any set whose frame count
# was 1 mod 12 simply could not be built from the session button. Chunk size only
# bounds working-set residency, so shrinking it is free.
# It must LOOP. A single decrement can land on a remainder of 1 again, because
# FRAMES = q*CHUNK + 1 gives FRAMES mod (CHUNK-1) = (q+1) mod (CHUNK-1), which is
# 1 whenever q is a multiple of CHUNK-1 — i.e. at the default CHUNK=12 for every
# FRAMES = 132k+1: 133, 265, 397. Those are ordinary set sizes here (july23's sets
# run 399-401), and the single-decrement version failed at the LAST chunk, hours
# in, after warping every earlier frame — strictly worse than the up-front abort
# it replaced. Floor of 2 because a chunk of 1 is the thing being avoided.
if [ $((FRAMES % CHUNK)) -eq 1 ]; then
  ORIGCHUNK=$CHUNK
  while [ "$CHUNK" -gt 2 ] && [ $((FRAMES % CHUNK)) -eq 1 ]; do CHUNK=$((CHUNK - 1)); done
  [ $((FRAMES % CHUNK)) -ne 1 ] || { echo "ABORT: $FRAMES frames leave a final chunk of 1 at every chunk size down to 2 — pass --frames to change the count" >&2; exit 1; }
  echo "chunk shrunk $ORIGCHUNK -> $CHUNK ($FRAMES frames leave a final chunk of 1 at $ORIGCHUNK, which cannot be sequenced; remainder is now $((FRAMES % CHUNK)))"
fi
PEAK_MIB=$(undistort_singlepass_peak_mib "$SESSION" "$SET") \
  || { echo "ABORT: cannot size the disk budget for $SET — see above" >&2; exit 1; }
NEED_GB=$(undistort_peak_gib "$SESSION" "$SET" "$FRAMES")
FREE_GB=$(df -BG --output=avail "$SESSION" | tail -1 | tr -dc 0-9)
[ "$FREE_GB" -ge "$NEED_GB" ] || { echo "ABORT: ~${NEED_GB}G peak needed for $FRAMES frames (${PEAK_MIB} MiB/frame, derived from this set's own frame geometry — disk_budget.sh), ${FREE_GB}G free — pass a smaller --frames (even stride keeps the full time span), or use run_undistort_groups.sh for full depth" >&2; exit 1; }

# ONE BUILDER PER session+set. $P is derived from SESSION and SET alone, so a
# second invocation would `rm -rf` the first's work dir MID-FLIGHT — the first then
# fails somewhere arbitrary with its inputs gone, which reads as a tool failure
# rather than a collision. Refuse instead. (Measured 2026-08-06: a rebuild died at
# "WARP FAILED" with its whole work tree missing while other work was in flight;
# the cause was unrecoverable because darktable's stderr was discarded — now kept.)
if [ -e "$P/.lock" ] && kill -0 "$(cat "$P/.lock" 2>/dev/null)" 2>/dev/null; then
  echo "ABORT: another build is already running for $SET (pid $(cat "$P/.lock")) and shares this work dir ($P). Wait for it, or use a different set." >&2
  exit 1
fi
rm -rf "$P"; mkdir -p "$P/out"; echo $$ > "$P/.lock"
trap 'rm -f "$P/.lock"' EXIT
mapfile -t ALL < <(python3 -c "
import sys
src = sys.argv[1:]; n = $FRAMES
for i in range(n): print(src[round(i*(len(src)-1)/(n-1))] if n > 1 else src[0])
" "${SRC[@]}")
echo "selected ${#ALL[@]} of ${#SRC[@]} lights (even stride over the full window)"

n=0; ci=0
while [ $n -lt ${#ALL[@]} ]; do
  ci=$((ci+1))
  rm -rf "$P/nef" "$P/proc" "$P/tif"; mkdir -p "$P/nef" "$P/proc" "$P/tif"
  for ((k=0; k<CHUNK && n<${#ALL[@]}; k++, n++)); do
    ln -sf "${ALL[$n]}" "$P/nef/$(basename "${ALL[$n]}")"
  done
  CAL=$(calibrate_light_cmd c "$DARK" -flat="$FLAT" -equalize_cfa -cfa -debayer -prefix=pp_)
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nconvert c -out=%s\ncd %s\n%s\n%b' \
    "$P/nef" "$P/proc" "$P/proc" "$CAL" "$SUBSKYCMD" > "$P/c.ssf"
  sir "$P/c.ssf"
  rm -f "$P/proc"/c_*.fit "$P/proc"/c_.seq
  # LAST POINT the acquisition keywords still exist: the warp below is a TIFF
  # round trip that carries no FITS header (stamp_headers.sh). Capture once —
  # from the pp_ files, which exist on every route (--subsky-lights adds
  # bkg_pp_ on top of them).
  [ -f "$ACQHDR" ] || header_capture "$(ls "$P/proc"/pp_c_*.fit | head -1)" "$ACQHDR"
  for f in "$P/proc"/${LPREFIX}c_*.fit; do
    b=$(basename "$f" .fit)
    printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\nload %s\nsavetif32 %s\n' "$f" "$P/tif/$b" > "$P/e.ssf"
    sir "$P/e.ssf"; rm -f "$f"
  done
  rm -f "$P/proc"/*.seq
  j=0
  for t in "$P/tif"/*.tif; do
    j=$((j+1))
    exiftool -q -overwrite_original -TagsFromFile "${SRC[0]}" -Make -Model -LensModel -FocalLength -FNumber -icc_profile:all= "$t" 2>/dev/null || true
    timeout 900 darktable-cli "$t" "$P/tif/w_$(printf %02d $ci)_$(printf %02d $j).tif" \
      --style lensdist --style-overwrite --icc-type LIN_REC709 --core \
      --configdir "$CFG" --library ":memory:" \
      --conf plugins/imageio/format/tiff/bpp=32 \
      --conf plugins/imageio/format/tiff/compress=0 > "$P/dt_last.log" 2>&1 \
      || { echo "WARP FAILED $b — darktable said:" >&2; tail -12 "$P/dt_last.log" >&2
           echo "  (input: $t, exists=$([ -f "$t" ] && echo yes || echo NO), configdir $CFG)" >&2
           exit 1; }
    rm -f "$t"
  done
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nconvert k%02d -out=%s\n' "$P/tif" "$ci" "$P/out" > "$P/v.ssf"
  sir "$P/v.ssf"
  rm -rf "$P/tif" "$P/nef" "$P/proc"
  echo "chunk $ci: $n/${#ALL[@]}  $(df -h "$SESSION" | tail -1 | awk '{print $4" free"}')"
done

python3 - "$P/out" <<'PY'
import os, re, sys
d = sys.argv[1]
fs = sorted((int(m.group(1)), int(m.group(2)), f) for f in os.listdir(d)
            if (m := re.match(r'k(\d+)_(\d+)\.fit$', f)))
for i, (c, j, f) in enumerate(fs, 1):
    os.rename(os.path.join(d, f), os.path.join(d, f'lt_{i:05d}.fit'))
print(f"one sequence: {len(fs)} frames")
PY
rm -f "$P/out"/*.seq
# The pre-registration frame-width crop (--crop-lr, Siril `seqcrop` between
# the darktable warp and register) is RETIRED — refuted at the cross-night
# combine: it starves a framing=max union's rims, whose only supply is the
# frame-edge bands it deletes. Mechanism + numbers:
# docs/dead-ends/stacking-compose.md (the frame-width-cropping entry);
# implementation recoverable at 6d9e568.
REJ=$(stack_rejection_for "$FRAMES")
# The A/B knobs. Both default to the production clause, so an ordinary build
# emits exactly the command it always did.
# NO -output_norm on the production path: it is a global min-max rescale — ONE
# (min, max) over all three channels — whose zero point is one darkest pixel
# (docs/dead-ends/stacking-compose.md, the -output_norm zero-point entry;
# docs/dead-ends/stacking-compose.md, the zero-point entry). Without it the sub-stack's level is
# its pinned reference FRAME's own IKSS location per channel, stamped below as
# ANCLOC*/ANCSCL* (ANCREF, ANCSRC); values outside [0,1] clamp. The --nonorm
# diagnostic arm is untouched.
# REMOVAL CONDITION: siril offers a reference-anchored (or per-channel,
# non-min-max) output normalization — then -output_norm returns and the ANC*
# anchor keys retire with it (the compose tier's condition, same wording).
NORMCLAUSE='-norm=addscale'
[ "$NONORM" = 0 ] || { NORMCLAUSE='-nonorm'
  echo "STACK NORMALIZATION DISABLED (-nonorm) — DIAGNOSTIC arm, not a deliverable"; }
# setref lt 1 AFTER the 2pass — the groups route's own pin (`setref s 1`), time
# order. The 2pass's quality pick is a lottery (12 of 13 canonical aug06 groups
# picked a frame other than 1 — 9/2/29/5/51, 25/77/11/18, 68/9/1/3, read from
# the members' inherited FILENAME cards) and with no -output_norm the reference
# frame is also the LEVEL anchor, so it must be a recorded choice. NOT on the
# --regdata path: the donor lt_.seq carries the donor's reference verbatim, and
# the printf's %b then emits neither register nor setref.
REGCMD='register lt -2pass -transf=homography\nsetref lt 1\n'
if [ -n "$REGDATA" ] && [ -f "$REGDATA" ]; then
  # Siril reads the registration data from <seq>.seq beside the images; the file
  # names (lt_NNNNN.fit) and the count are identical across arms by construction,
  # so the donor's homographies and reference index apply verbatim.
  cp "$REGDATA" "$P/out/lt_.seq"; REGCMD=
  echo "registration PINNED from $REGDATA — this arm does not re-register (ref frame + every transform are the donor's)"
fi
printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\n%bseqapplyreg lt -framing=min -prefix=r_ -interp=lanczos4\nstack r_lt %s %s -out=%s\n' \
  "$P/out" "$REGCMD" "$REJ" "$NORMCLAUSE" "$OUT" > "$P/s.ssf"
sir "$P/s.ssf"
[ -f "$OUT.fit" ] || { echo "STACK MISSING — read $P/siril.log" >&2; exit 1; }
# POST-ASSERT on siril's own log line. $P is recreated per run (rm -rf above)
# and every sir() of this run appends to $P/siril.log; only `stack` prints the
# line (on the -nonorm arm too), so no offset scoping is needed here.
grep -q "Output normalization ...... disabled" "$P/siril.log" \
  && ! grep -q "Output normalization ...... enabled" "$P/siril.log" || {
  echo "ABORT: siril did not report 'Output normalization ...... disabled' — the" >&2
  echo "  sub-stack's zero point would be the min-max lottery this route retired" >&2
  echo "  (docs/dead-ends/stacking-compose.md). Read $P/siril.log" >&2; exit 1; }
# THE REFERENCE AND THE ANCHOR — captured into variables NOW: `rm -rf "$P/out"`
# below deletes lt_.seq / r_lt_.seq, and the stamp (header_apply_keys "$PROV")
# runs after the acquisition-key save. `stack` normalized on the r_lt sequence,
# whose .seq holds siril's own M lines (M<layer>-<image0>: total ngoodpix mean
# median sigma avgDev mad sqrtbwmv location scale min max normValue bgnoise);
# its S line (field 7, 0-based) is the reference the stack used and is what
# ANCREF stamps; lt_.seq's is the pin (or the donor's under --regdata); a
# disagreement is printed. REGREF names the FRAME as <1-based index>:<raw
# basename> from ALL, the ordered list this run stacked (= SRC under --select;
# an even stride over SRC under --frames=N) (FILENAME already
# carries the reference's w_<chunk>_<j>.tif; this says which raw). Values are
# siril's own [0,1] floats; x65535 for ADU16.
REFID= REFSRC= ANCHOR= ANCREF=
REF0=$(awk '$1=="S" && NF>=7 {print $7; exit}' "$P/out/lt_.seq" 2>/dev/null || true)
RS0=$(awk '$1=="S" && NF>=7 {print $7; exit}' "$P/out/r_lt_.seq" 2>/dev/null || true)
if [ -n "${RS0:-}" ] && [ "$RS0" -ge 0 ] 2>/dev/null && [ "$RS0" -lt "${#ALL[@]}" ]; then
  [ "$RS0" = "${REF0:-}" ] || echo "WARNING: r_lt_.seq reference $RS0 != lt_.seq reference ${REF0:-?} (0-based) — the stack normalized against $RS0; ANCREF stamps that, REGREF the pin" >&2
  ANCREF=$((RS0 + 1))
  ANCHOR=$(awk -v r="$RS0" '$1=="M0-"r{l0=$10;s0=$11} $1=="M1-"r{l1=$10;s1=$11} $1=="M2-"r{l2=$10;s2=$11}
    END{ if (l0!="" && l1!="" && l2!="") printf "update_key ANCLOCR %s\nupdate_key ANCLOCG %s\nupdate_key ANCLOCB %s\nupdate_key ANCSCLR %s\nupdate_key ANCSCLG %s\nupdate_key ANCSCLB %s\n", l0, l1, l2, s0, s1, s2 }' "$P/out/r_lt_.seq")
  [ -n "$ANCHOR" ] || echo "WARNING: no M lines for reference $RS0 in $P/out/r_lt_.seq — ANCLOC*/ANCSCL* unstamped" >&2
else
  echo "WARNING: could not read the reference from $P/out/r_lt_.seq — anchor unstamped" >&2
fi
if [ -n "${REF0:-}" ] && [ "$REF0" -ge 0 ] 2>/dev/null && [ "$REF0" -lt "${#ALL[@]}" ]; then
  REFID="$((REF0 + 1)):$(basename "${ALL[$REF0]}")"
  REFSRC=$([ -n "$REGDATA" ] && echo regdata || echo pinned)
fi
# the .seq files die with $P/out below; the run log carries the anchor too
echo "anchor: REGREF=${REFID:-unstamped} [${REFSRC:-?}] ANCREF=${ANCREF:-unstamped} ANCLOC R,G,B = $(printf '%s\n' "$ANCHOR" | awk '/ANCLOC/{printf "%s ", $3}')"
if [ -n "$REGDATA" ] && [ ! -f "$REGDATA" ]; then
  mkdir -p "$(dirname "$REGDATA")"
  cp "$P/out/lt_.seq" "$REGDATA"
  echo "registration data SAVED to $REGDATA — hand it to every other arm of this A/B"
fi
if [ "$KEEPOUT" = 1 ]; then
  echo "work dir KEPT at $P/out (--keep-out): lt_ frames, r_lt_ registered copies, lt_.seq and r_lt_.seq — delete by hand"
else
  rm -rf "$P/out"
fi
# restore the acquisition keywords the warp dropped (Siril's own update_key),
# and stamp the OPTICS + CALIBRATION provenance beside them. The provenance half
# is unconditional: it does not depend on the pre-warp capture, and a sub-stack
# that cannot say what warped it cannot be composed safely months later
# (stamp_headers.sh; the compose gate reads exactly these keys).
PROV=$(header_provenance_lines "$REPO" "$SESSION" "$SET" "$([ "$SUBSKYL" = 1 ] && echo subsky1-nodither || echo none)" "$DARK" "$FLAT")
# The A/B keys go on ONLY when an A/B flag was passed, so an ordinary product's
# header is unchanged. A diagnostic arm has to be able to say what it is without
# anyone remembering which work dir it came out of — the same argument BKGLIGHT
# and DISTPROV are on the product rather than in a build log.
[ "$NONORM" = 0 ] || PROV="$PROV
update_key STACKNRM \"nonorm\"
update_key DIAGARM T"
[ "$NONORM" = 0 ] && PROV="$PROV
update_key STACKNRM \"addscale\""
# REGMODEL/REGUNDIS/REGREF/REGREFSR + the anchor, on the sub-stack too — INFORMATIONAL
# (the compose gate's REQUIRED list is untouched); the union's ANCREF then
# points at a member that can say its own anchor.
PROV="$PROV
$(header_registration_lines starpair F "$REFID" "$REFSRC")
update_key ANCSRC \"r_lt_.seq M-line IKSS loc/scale of ANCREF; [0,1] float, x65535=ADU16\"
${ANCREF:+update_key ANCREF $ANCREF}
$ANCHOR"
[ -z "$REGDATA" ] || PROV="$PROV
update_key REGPIN \"$(basename "$REGDATA")\""
# CALFLAT/CALDARK NOW DESCRIBE THE MASTERS THAT RAN — they are passed to
# header_provenance_lines above, so the product cannot claim a calibration it did
# not get and there is nothing left to correct downstream. CALXSET IS DEPRECATED
# AS A WRITE TARGET and is no longer stamped: it encoded a RELATION between the
# product and a MUTABLE record, and that relation is unnecessary once the keys are
# true by construction. It stays READABLE — products already carry it.
#
# THE GUARD IT REPLACES WAS BLIND ON THE CASE IT EXISTED TO CATCH. It compared
# `basename "$FLAT"`, which answers "do these two flats share a filename" rather
# than "is this the flat this set recorded" — and 19 masters here carry 12
# distinct basenames, with `dark_master.fit` identical across all three sessions.
# A cross-NIGHT calibration (banned for deliverables, README step 1b) makes the
# two strings EQUAL, so the guard stayed silent on exactly the banned case. The
# operator NOTE below compares RESOLVED PATHS, which is the quantity that was
# always wanted; `$FLAT` has been absolute since :153.
RECFLAT=$(python3 - "$REPO" "$SESSION" "$SET" <<'PY'
import json, os, sys
repo, session, sset = sys.argv[1:4]
ses = os.path.basename(os.path.abspath(session))
p = os.path.join(repo, "datasets", ses, sset, "qa_work", "skyflat_%s_qa.json" % sset)
try:
    f = (json.load(open(p)) or {}).get("flat") or ""
    print(os.path.abspath(f) if f else "")
except Exception:
    print("")
PY
)
if [ -n "$RECFLAT" ] && [ "$RECFLAT" != "$FLAT" ]; then
  echo "NOTE: --flat=$FLAT is not the flat this set's record names ($RECFLAT) — CALFLAT/CALFSUM describe the flat that RAN (cross-set calibration: banned for deliverables, README step 1b; DIAGNOSTIC arms only)"
fi
if [ -f "$ACQHDR" ]; then
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\nload %s\n%s\nsave %s\n' \
    "$OUT.fit" "$(header_stamp_lines "$ACQHDR" "$FRAMES")" "$OUT" > "$P/h.ssf"
  sir "$P/h.ssf"
  echo "stamped acquisition keywords onto $(basename "$OUT.fit") (LIVETIME = $FRAMES x EXPTIME)"
else
  echo "WARNING: no acquisition-header capture — $OUT.fit ships without FOCALLEN/XPIXSZ (solve loses its scale hint)" >&2
fi
# The provenance half goes through a FITS library, NEVER siril: CALSET is
# `<session>/<set>` and siril `update_key` cuts a string value at the first `/`
# (it begins the FITS comment field) — the registered silent truncation.
# MEASURED here: members stamped through the .ssf shipped CALSET='july31', the
# set identity gone, and every composite CALSETS above them inherited the loss.
# Acquisition keys stay on update_key: siril's own data, slash-free by
# construction.
if [ -n "$PROV" ]; then
  header_apply_keys "$OUT.fit" "$PROV"
  echo "stamped optics/calibration provenance ($(printf '%s\n' "$PROV" | grep -c update_key) keys — DISTA/B/C from the VERIFIED live model, not the record's intent)"
else
  echo "WARNING: no optics provenance stamped — this sub-stack cannot state what warped it, and the compose gate will treat it as UNKNOWN, never as compatible" >&2
fi
echo "=== DONE: $OUT.fit ==="
ls -la "$OUT.fit"
# State what optical state the MACHINE is left carrying. The DB is global and
# nothing reverts it, so the next non-chain darktable render on this rig gets
# this model, for any session. Announced, never silent.
echo "lensfun DB now holds: $(grep -ho 'astro-imaging fitted:[^>]*' "$HOME/.local/share/lensfun/updates/version_1"/*.xml 2>/dev/null | sed 's/ *-*$//' | tail -1)"
df -h "$SESSION" | tail -1
