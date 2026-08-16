#!/usr/bin/env bash
# Compose each arm's five sub-stacks into its product — with the COMPOSE
# registration pinned across arms, which the shipped groups driver has no flag
# for and which this measurement cannot do without.
#
# WHY. run_undistort_groups.sh's final step runs `register s -2pass` over the
# five sub-stacks. Those sub-stacks DIFFER between arms (that is the experiment),
# so each arm would estimate its own homographies and the two composed products
# would not be pixel-comparable — the same defect `--regdata=` fixes one level
# down, one level up. Arm A registers; every other arm is handed arm A's `s_.seq`
# and only applies it.
#
# The registered members are KEPT (the shipped driver deletes them): they are the
# only surface on which members of one arm can be compared with each other, since
# each group's own sub-stack has its own -framing=min canvas.
#
# -nonorm at the compose too, to match the arms: the pixel instrument is valid
# only where nothing has renormalized the difference under test.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
S=$REPO/sessions/july31
W=$S/work/pergroup
source "$REPO/scripts/lib/siril_run.sh"
REGSEQ=$W/armreg_compose.seq

compose() {   # <arm-dir> <norm-clause>
  local dir=$1 norm=$2
  local seqd=$W/$dir/seq out=$W/$dir/compose_$dir
  [ -f "$out.fit" ] && { echo "=== compose $dir exists, skipping ==="; return 0; }
  rm -rf "$W/$dir/link" "$seqd"; mkdir -p "$W/$dir/link" "$seqd"
  for f in "$W/$dir"/sub_0*.fit; do ln -sf "$f" "$W/$dir/link/$(basename "$f")"; done
  local reg='register s -2pass -transf=homography\nsetref s 1\n'
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\nlink s -out=%s\n' \
    "$W/$dir/link" "$seqd" > "$W/$dir/link.ssf"
  siril_cli -d "$W/$dir" -s "$W/$dir/link.ssf" > "$W/$dir/link.log" 2>&1
  if [ -f "$REGSEQ" ]; then
    cp "$REGSEQ" "$seqd/s_.seq"; reg=
    echo "  compose registration PINNED from $(basename "$REGSEQ")"
  fi
  # framing=min and interp pinned exactly as the shipped groups compose emits
  # them; the ONLY departure is -nonorm and the pinned registration.
  printf 'requires 1.2.0\nset32bits\nsetcompress 0\nsetext fit\ncd %s\n%bseqapplyreg s -framing=min -prefix=r_ -interp=lanczos4\nstack r_s mean none %s -out=%s\n' \
    "$seqd" "$reg" "$norm" "$out" > "$W/$dir/compose.ssf"
  siril_cli -d "$seqd" -s "$W/$dir/compose.ssf" > "$W/$dir/compose.log" 2>&1
  [ -f "$out.fit" ] || { echo "COMPOSE $dir FAILED — read $W/$dir/compose.log" >&2; exit 1; }
  [ -f "$REGSEQ" ] || { cp "$seqd/s_.seq" "$REGSEQ"
    echo "  compose registration SAVED to $(basename "$REGSEQ")"; }
  rm -rf "$W/$dir/link"
  echo "  $(basename "$out.fit"): $(python3 -c "
from astropy.io import fits;h=fits.getheader('$out.fit');print(h['NAXIS1'],'x',h['NAXIS2'])")  registered members kept in $seqd"
}

compose armA -nonorm      # registers, and donates the registration
compose armB -nonorm
compose armI -nonorm      # identity: predicted bit-identical to armA's compose
# PIXELS, not bytes. A whole-file `cmp` is the WRONG test and fires a false
# alarm: Siril stamps its own creation DATE on every product, and the chain
# stamps PIPEREV (the repo revision), so two pixel-identical products always
# differ as files. MEASURED on the member-level identity control: 0 differing
# pixels of 3 x 3965 x 5831, max|diff| exactly 0, with DATE and PIPEREV the only
# header differences — which also measures the commits made between the two arms
# PIXEL-NEUTRAL for this route.
python3 - "$W/armA/compose_armA.fit" "$W/armI/compose_armI.fit" <<'PY'
import sys
import numpy as np
from astropy.io import fits
a, b = (fits.getdata(p).astype("float64") for p in sys.argv[1:3])
d = a - b
n = int((d != 0).sum())
print(f"COMPOSED IDENTITY: {n} differing pixels of {a.size}, "
      f"max|diff| {np.abs(d).max():.6g}"
      + ("  — a TRUE ZERO" if n == 0 else "  — NOT zero, find out why before "
         "reading any number"))
PY
echo "=== COMPOSES DONE ==="
ls -la "$W"/arm*/compose_*.fit
