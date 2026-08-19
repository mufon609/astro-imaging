#!/bin/bash
# ONE-TIME backfill of composite identity onto composites built before the
# stamp carried it (the backfill_substack_provenance.sh precedent: a FITS
# library writes headers; no pixel is read for anything but the integrity
# check, and no pixel is written). What it applies is exactly what the fixed
# header_composite_provenance_lines emits from the product's OWN members —
# CALSET common-or-MIXED(n), DATE-OBS = earliest member start, GRPSIZE and
# FILENAME deleted — with ONE substitution: the emitter derives PIPEREV from
# HEAD, which is only true at compose time, so this script takes the product's
# RECORDED build commit as an argument and writes that, or DELETES the key
# when the build commit is unrecorded ('-'): an absent stamp beats a
# confidently false one (the stamp's own doctrine).
#
#   backfill_composite_identity.sh <piperev|-> <product.fit> <member.fit>...
#
# INTEGRITY: the sha256 of the primary HDU's DATA BYTES is computed before and
# after the header rewrite and the script FAILS on any difference — the header
# block may grow by a 2880-byte block, the data must not move a bit.
# Registration keys (REGMODEL/REGUNDIS/REGREF) are deliberately NOT touched:
# they need the compose's own .seq, which is deleted at the end of a run.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)
# shellcheck source=stamp_headers.sh
source "$REPO/scripts/stack/stamp_headers.sh"

REV=${1:?usage: backfill_composite_identity.sh <piperev|-> <product.fit> <member.fit>...}
PROD=${2:?product.fit required}
shift 2
[ $# -ge 2 ] || { echo "need at least 2 members" >&2; exit 1; }

data_sha() {
  python3 - "$1" <<'PY'
import hashlib, sys
from astropy.io import fits
with fits.open(sys.argv[1], memmap=True) as hd:
    print(hashlib.sha256(hd[0].data.tobytes()).hexdigest()[:16])
PY
}

LINES=$(header_composite_provenance_lines "$REPO" "$@" | grep -v '^update_key PIPEREV ')
if [ "$REV" = "-" ]; then
  LINES="$LINES
delete_key PIPEREV"
else
  LINES="$LINES
update_key PIPEREV \"$REV\""
fi

before=$(data_sha "$PROD")
header_apply_keys "$PROD" "$LINES"
after=$(data_sha "$PROD")
if [ "$before" != "$after" ]; then
  echo "FATAL: data block changed on $PROD ($before -> $after)" >&2
  exit 1
fi

python3 - "$PROD" <<'PY'
import sys
from astropy.io import fits
h = fits.getheader(sys.argv[1])
print("  read-back:", " ".join(
    f"{k}={h.get(k, '<absent>')}" for k in
    ("NMEMBER", "PIPEREV", "CALSET", "CALSETS", "DATE-OBS", "GRPSIZE", "FILENAME")))
PY
echo "OK $PROD  data-sha unchanged ($before)  members=$#"
