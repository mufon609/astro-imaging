#!/usr/bin/env bash
# Shared disk-budget derivation for the undistort route. SOURCED, never executed
# (the precedent is calibrate_light.sh / stack_rejection.sh: one definition, every
# consumer, no drift).
#
# WHY THIS FILE EXISTS. The single-pass peak was written twice — once in the
# builder that ENFORCES it (run_undistort_pipeline.sh) and once in the router that
# DECIDES on it (run_set_chain.sh) — and the two silently diverged. 231 MB/frame
# was the 16-bit-intermediates figure; when 16-bit was retired the builder doubled
# to 462 and the router kept 231, so between those two figures the chain routed a
# set to the single-pass builder that then aborted its own preflight. The router
# predated the retirement, which is the repo's root-cause rule firing: when a
# cause is fixed, every knob derived while it was present is stale.
#
# WHY IT IS DERIVED AND NOT A CONSTANT. Any fixed MiB/frame number is really a
# statement about one sensor. 561 MiB/frame — the figure this file briefly
# carried — is 6064x4040x3x4x2, i.e. the Z6III's geometry frozen into a constant.
# It under-states a 61 MP body by ~2.5x (which would abort mid-warp, the exact
# failure the up-front guard exists to prevent) and over-states a small mono
# astrocam by an order of magnitude (which would refuse a run that fits, or push
# it to the slower groups route for nothing). The repo's north star is that ANY
# dataset can be dropped into a session dir, so the budget has to come from the
# DATA. Only the multipliers are universal:
#
#   peak_per_frame = W x H x C x 4 bytes x 2
#
#     W x H  the frame geometry, read from the set's own tracked acquisition
#            record (`exif.image_wh`). That fact is already derived for every
#            data class the repo accepts — exiftool for camera raws, the FITS
#            header's NAXIS1/NAXIS2 for dedicated-astrocam frames
#            (scripts/lib/acquisition.py) — so this adds no new instrument and
#            reads no pixel.
#     C      channels once the route's debayer has run: 3 for a CFA/OSC raw,
#            NAXIS3 (or 1, mono) for a FITS set. A mono corpus therefore budgets
#            a third of an OSC one instead of inheriting a colour assumption.
#     4      bytes per sample: the 32-bit float contract, enforced end to end by
#            check_bitdepth.sh. If a rig ever re-adopts 16-bit this term moves
#            with it — and that adaptation needs its own removal condition.
#     2      the two frame-sets held resident at once. This is the route's
#            structure, not the data's: `seqapplyreg lt -framing=min -prefix=r_`
#            writes the registered set BESIDE the warped set and both stay on
#            disk until `stack` finishes. It is an upper bound, because
#            -framing=min crops the registered set to the intersection, so the
#            second set is <= the first. A far-drifting set therefore has real
#            headroom against this figure; a low-drift one approaches it.
#
# VALIDATED against measured artifacts on the 24.5 Mpx class this rig shoots:
# W x H x C x 4 predicts 280.4 MiB and the warped frames measure 280.37 MiB
# (sessions/july14/work/undistort_set-01/out/k01_00001.fit). The registered term
# measured 200.7 MiB on july31/set-01 (its 4915x3568x3 -framing=min canvas), so
# that set's true peak was 481 MiB/frame against the 561 this formula bounds it
# at — the intended direction for an abort threshold, since the canvas is not
# knowable before registration runs, a false abort prints one line, and a false
# PASS dies hours into warping. A set that trips the bound is not stuck: it
# routes to run_undistort_groups.sh (full depth, one extra interpolation pass) or
# takes --frames=N.
#
# It STOPS rather than guessing when the geometry is not on record — a silently
# wrong budget is what this file exists to prevent, so falling back to a default
# would reintroduce the defect in a new costume.

# Resolved when this file is SOURCED, from its own location — so the record path
# never depends on the caller's cwd or on the session dir sitting in a particular
# place relative to the repo.
_DISK_BUDGET_REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

# undistort_frame_mib <session-dir> <set> — ONE uncompressed frame on disk, MiB,
# derived from the set's own recorded geometry. This is the BASE quantity; every
# budget below is a multiple of it, so no route carries its own per-frame number.
# Prints the value; exits nonzero with a reason if the geometry is not on record.
# An optional third argument OVERRIDES the derived channel count. It exists for
# the one resident form that is not the route's debayered frame: build_sky_flat.sh
# keeps its working set as CFA (`calibrate` with no `-debayer`, because an OSC flat
# must divide the mosaic before any interpolation), so its per-frame residency is
# W x H x 1 x 4, a third of the undistort route's. Passing the channel count keeps
# ONE derivation of W and H rather than giving the flat builder a private formula —
# which is how it ended up carrying `98` (this sensor's 32-bit CFA frame, under a
# comment claiming 49 MB and 16-bit) while this file existed to prevent exactly
# that. 98 is right for a 6064x4040 body and wrong for every other one: it
# understates a 61 MP frame 2.5x, which fails mid-run, and overstates a small mono
# astrocam.
undistort_frame_mib() {
  python3 - "$_DISK_BUDGET_REPO" "$1" "$2" "${3:-}" <<'PY'
import glob, json, os, sys

repo, session, sset = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]
acq_path = os.path.join(repo, "datasets", os.path.basename(session), sset,
                        "acquisition.json")
try:
    acq = json.load(open(acq_path))
except (OSError, ValueError) as e:
    sys.exit(f"disk_budget: no usable acquisition record at {acq_path} ({e}) — "
             "the per-frame disk budget is derived from exif.image_wh, so this "
             "STOPS rather than assume a frame size. Run the chain preflight "
             "(scripts/lib/acquisition.py) for this set first.")
wh = (acq.get("exif") or {}).get("image_wh") or []
if len(wh) != 2 or not all(isinstance(v, int) and v > 0 for v in wh):
    sys.exit(f"disk_budget: {acq_path} has no usable exif.image_wh ({wh!r}) — "
             "the frame geometry is what sizes the budget. Re-run the "
             "acquisition derivation; if the tool cannot read this format, that "
             "is a documented gap, not a default to invent.")
w, h = wh

# Channels AFTER the route's debayer. Camera raws are CFA and the route debayers
# them to 3; a FITS set is whatever its header says (mono = 1). Decided by what
# is actually staged, so a mono corpus is not charged for colour it never has.
RAW = ("*.nef", "*.dng", "*.cr2", "*.cr3", "*.arw", "*.raf")
staged = [f for pat in RAW
          for f in glob.glob(os.path.join(session, sset, pat))
          + glob.glob(os.path.join(session, sset, pat.upper()))]
if staged:
    channels, why = 3, "CFA raw debayered by the route"
else:
    fits_files = sorted(glob.glob(os.path.join(session, sset, "*.fit"))
                        + glob.glob(os.path.join(session, sset, "*.fits")))
    if not fits_files:
        sys.exit(f"disk_budget: no raw or FITS frames under {session}/{sset} — "
                 "nothing to size a budget for.")
    try:
        from astropy.io import fits
        hdr = fits.getheader(fits_files[0])          # HEADER only, no pixels
        channels = int(hdr.get("NAXIS3") or 1)
    except Exception as e:
        sys.exit(f"disk_budget: could not read NAXIS3 from {fits_files[0]} "
                 f"({e}) — channel count is part of the budget, so this STOPS.")
    why = f"FITS NAXIS3={channels}" + (" (mono)" if channels == 1 else "")

override = sys.argv[4] if len(sys.argv) > 4 else ""
if override:
    channels, why = int(override), f"caller override, {override} channel(s)"

BYTES_PER_SAMPLE = 4     # 32-bit float, enforced by check_bitdepth.sh
print(int(w * h * channels * BYTES_PER_SAMPLE / 1048576))
# the geometry this resolved to, for debugging a budget that looks wrong. OFF by
# default: the callers already print MiB/frame in their own plan lines, and this
# function is called several times per run, so unconditional stderr would leak a
# repeated line into every plan.
if os.environ.get("DISK_BUDGET_VERBOSE") == "1":
    print(f"disk_budget: {w}x{h}x{channels} f32 ({why})", file=sys.stderr)
PY
}

# sky_flat_frame_mib <session-dir> <set> — ONE resident CFA frame for
# build_sky_flat.sh, MiB. Same geometry derivation, one channel (no debayer).
sky_flat_frame_mib() { undistort_frame_mib "$1" "$2" 1; }

# undistort_singlepass_peak_mib <session-dir> <set> — the single-pass route's
# high-water mark: TWO frames, because `seqapplyreg` writes the registered set
# beside the warped set and both stay resident until `stack` finishes.
undistort_singlepass_peak_mib() {
  local f; f=$(undistort_frame_mib "$1" "$2") || return 1
  echo $(( f * 2 ))
}

# undistort_groups_peak_gib <session-dir> <set> <max-group> <ngroups> — the
# GROUPS route's high-water mark, same geometry, different shape. Two phases:
#   per-group  one group runs the full single-pass chain -> max_group x 2 frames,
#              and its intermediates are deleted before the next group starts;
#   final      all K sub-stacks resident, then registered copies written beside
#              them -> K x 2 frames.
# Both phases are bounded by the FULL frame because `-framing=min` only ever
# crops. Hardcoded figures (290 / 145 / 85 MB) describe this rig's sensor only
# and, in the per-group case, name two resident frames while budgeting for one —
# which is why the route derives its numbers here instead.
undistort_groups_peak_gib() {
  local f; f=$(undistort_frame_mib "$1" "$2") || return 1
  local per_group=$(( ($3 * 2 * f + $4 * f) / 1024 + 2 ))
  local final=$(( $4 * 2 * f / 1024 + 2 ))
  echo $(( per_group > final ? per_group : final ))
}

# undistort_peak_gib <session-dir> <set> <nframes> — GiB the single-pass route
# needs, including 2 GiB of slack for .seq files, logs and the final stack.
# The ARITHMETIC is shared, not just the geometry: with the router comparing
# against a bare nframes*peak while the builder demanded peak+2, a 2 GiB window
# remained in which the router still chose single-pass and the builder still
# aborted — the same defect this file exists to remove, only smaller.
undistort_peak_gib() {
  local mib
  mib=$(undistort_singlepass_peak_mib "$1" "$2" 2>/dev/null) || return 1
  echo $(( $3 * mib / 1024 + 2 ))
}
