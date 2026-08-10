#!/usr/bin/env bash
# Pull a capture session from the remote publisher, verified — the LOCAL half.
#
#   fetch_session.sh <session> [--host HOST:PORT] [--units darks,set-01,...]
#                    [--watch] [--retries 3] [--dry-run]
#
# Pairs with scripts/ingest/remote_publish.sh, which hashes each frame AT THE
# SOURCE and serves a `sha256sum`-format manifest per unit. This side fetches
# the manifest first, then the frames, then verifies the landed copies against
# that manifest with coreutils `sha256sum -c`. The integrity check therefore
# compares source-computed hashes to destination-computed hashes — a check that
# re-hashed the copy on both ends would only prove the copy equals itself.
#
# Frames land in sessions/<session>/<unit>/, which is raws-only by repo
# contract; every record and every scratch file this produces lives under
# datasets/<session>/<unit>/ingest_work/ instead.
#
# RESUMABLE AND IDEMPOTENT, because the capture is still running. Re-running is
# the normal mode of operation: a file whose local sha256 already matches the
# manifest is skipped without a byte moving, a partial download resumes from its
# .part file (curl -C -), and units the publisher has not sealed yet are
# reported incomplete rather than declared done. --watch keeps re-passing a unit
# until the publisher seals it AND every file in it verifies, then moves to the
# next unit in the order given.
#
# ORDER IS EXPLICIT, NOT ALPHABETICAL. Darks first: they gate calibration, they
# are usually already complete when lights are still landing, and a verified
# dark library is what makes a partial light set useful at all.
#
# A file is only moved into place after its own hash matches, so the session dir
# never contains an unverified frame — an interrupted run leaves .part files,
# never a corrupt NEF that a later pass would trust.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && cd .. && pwd)
cd "$REPO"

SESSION=${1:?usage: fetch_session.sh <session> [--host HOST:PORT] [--units a,b] [--watch]}
shift || true
HOST=100.71.69.25:8000
UNITS="darks,set-01,set-02,set-03,set-04,set-05"
RETRIES=3 WATCH=0 DRY=0 POLL=60
for a in "$@"; do case "$a" in
  --host=*)    HOST=${a#*=};;
  --units=*)   UNITS=${a#*=};;
  --retries=*) RETRIES=${a#*=};;
  --poll=*)    POLL=${a#*=};;
  --watch)     WATCH=1;;
  --dry-run)   DRY=1;;
  *) echo "fetch_session: unknown arg $a" >&2; exit 2;;
esac; done

BASE=http://$HOST
CURL=(curl -fsS --connect-timeout 10 --max-time 900 --retry 2 --retry-delay 3)

link_up() { "${CURL[@]}" -o /dev/null "$BASE/.publish/INDEX.json"; }

if ! link_up; then
  cat >&2 <<EOF
fetch_session: no publisher at $BASE/.publish/INDEX.json

  The remote half is not running. On the capture host:
    remote_publish.sh <capture-root> --port ${HOST##*:}

  (host reachable? try: ping -c2 ${HOST%%:*})
EOF
  exit 1
fi

# ---- per unit ---------------------------------------------------------------
GRAND_OK=0 GRAND_BAD=0 GRAND_BYTES=0 INCOMPLETE=()

unit_sealed() {  # <unit>
  "${CURL[@]}" "$BASE/.publish/INDEX.json" \
    | python3 -c 'import json,sys;print(json.load(sys.stdin)["units"].get(sys.argv[1],{}).get("sealed",False))' "$1" 2>/dev/null
}

fetch_unit() {  # <unit> -> 0 fully verified + sealed, 1 incomplete, 2 error
  local unit=$1
  local dest=$REPO/sessions/$SESSION/$unit
  local work=$REPO/datasets/$SESSION/$unit/ingest_work
  local man=$work/$unit.sha256
  mkdir -p "$dest" "$work"

  if ! "${CURL[@]}" -o "$man.tmp" "$BASE/.publish/$unit.sha256"; then
    echo "  [$unit] no manifest published yet"
    rm -f "$man.tmp"; return 1
  fi
  mv -f "$man.tmp" "$man"

  local total; total=$(wc -l < "$man")
  if [ "$total" -eq 0 ]; then echo "  [$unit] manifest empty — nothing settled yet"; return 1; fi

  # Reject names that would need URL escaping rather than silently mangling one.
  if grep -qE '^[0-9a-f]{64}  .*[^A-Za-z0-9._-]' "$man"; then
    echo "  [$unit] manifest contains names needing URL escaping — refusing" >&2
    grep -nE '^[0-9a-f]{64}  .*[^A-Za-z0-9._-]' "$man" | head -5 >&2
    return 2
  fi

  local got=0 skip=0 bad=0 bytes=0 n=0 t0 hash name
  t0=$(date +%s)
  # sha256sum format is "<hash><space><space><name>"; the name-charset guard
  # above is what makes a plain two-field read safe here.
  while read -r hash name; do
    n=$((n + 1))
    local target=$dest/$name part=$dest/.$name.part
    if [ -f "$target" ] && [ "$(sha256sum "$target" | cut -d' ' -f1)" = "$hash" ]; then
      skip=$((skip + 1)); continue
    fi
    if [ "$DRY" = 1 ]; then got=$((got + 1)); continue; fi

    # Resume is worth one attempt on a big frame over a slow link, but it must
    # not be able to loop: a .part already at full length makes the server
    # answer 416 to every further ranged request, and a .part whose bytes are
    # wrong can never hash correctly no matter how much is appended. So a failed
    # or non-verifying resume drops the part and the next try starts clean.
    local try=0 ok=0
    while [ $try -lt "$RETRIES" ]; do
      try=$((try + 1))
      local resume=(); [ -f "$part" ] && resume=(-C -)
      if "${CURL[@]}" "${resume[@]}" -o "$part" "$BASE/$unit/$name"; then
        if [ "$(sha256sum "$part" | cut -d' ' -f1)" = "$hash" ]; then ok=1; break; fi
        rm -f "$part"
      elif [ $try -ge 2 ]; then
        rm -f "$part"
      fi
      sleep 2
    done
    if [ $ok -eq 1 ]; then
      bytes=$((bytes + $(stat -c '%s' "$part")))
      mv -f "$part" "$target"; got=$((got + 1))
    else
      echo "  [$unit] FAILED after $RETRIES tries: $name" >&2
      bad=$((bad + 1))
    fi
    if [ $((n % 25)) -eq 0 ]; then
      local el=$(( $(date +%s) - t0 )); [ "$el" -eq 0 ] && el=1
      printf '  [%s] %d/%d  new=%d have=%d fail=%d  %.1f MiB/s\n' \
        "$unit" "$n" "$total" "$got" "$skip" "$bad" \
        "$(awk -v b="$bytes" -v e="$el" 'BEGIN{printf "%.1f", b/1048576/e}')"
    fi
  done < "$man"

  # End-to-end verdict from the standard checker, over the whole landed unit.
  local report=$work/verify.txt rc=0
  ( cd "$dest" && sha256sum -c "$man" ) > "$report" 2>&1 || rc=$?
  local vok vbad
  # Count the checker's own per-file verdicts only — its trailing WARNING
  # summary lines are not files and must not inflate the failure count.
  vok=$(grep -c ': OK$'                       "$report" || true)
  vbad=$(grep -cE ': (FAILED|FAILED open or read)$' "$report" || true)

  local sealed; sealed=$(unit_sealed "$unit")
  local elapsed=$(( $(date +%s) - t0 )); [ "$elapsed" -eq 0 ] && elapsed=1

  SESSION="$SESSION" python3 - "$work/ingest.json" "$unit" "$total" "$got" "$skip" "$bad" \
      "$vok" "$vbad" "$bytes" "$elapsed" "$sealed" "$HOST" "$rc" <<'PY'
import json, os, sys
p, unit, total, got, skip, bad, vok, vbad, byts, el, sealed, host, rc = sys.argv[1:]
json.dump({
  "session": os.environ["SESSION"], "unit": unit, "source": f"http://{host}/{unit}",
  "manifest_algo": "sha256", "manifest_entries": int(total),
  "downloaded": int(got), "already_present": int(skip), "download_failed": int(bad),
  "verified_ok": int(vok), "verified_bad": int(vbad),
  "verify_exit": int(rc), "bytes_transferred": int(byts), "seconds": int(el),
  "mib_per_s": round(int(byts) / 1048576 / max(int(el), 1), 2),
  "remote_sealed": sealed.strip().lower() == "true",
  "complete": sealed.strip().lower() == "true" and int(vbad) == 0 and int(bad) == 0,
  "_note": "hashes computed at the source by scripts/ingest/remote_publish.sh; "
           "verified here with coreutils sha256sum -c. `complete` requires the "
           "publisher to have sealed the unit AND every entry to verify.",
}, open(p, "w"), indent=1)
PY

  printf '  [%s] entries=%d new=%d had=%d fail=%d  verify: OK=%d BAD=%d  sealed=%s\n' \
    "$unit" "$total" "$got" "$skip" "$bad" "$vok" "$vbad" "$sealed"

  GRAND_OK=$((GRAND_OK + vok)); GRAND_BAD=$((GRAND_BAD + vbad + bad))
  GRAND_BYTES=$((GRAND_BYTES + bytes))
  [ "$vbad" -eq 0 ] && [ "$bad" -eq 0 ] && [ "${sealed,,}" = "true" ] && return 0
  return 1
}

echo "fetch_session: $SESSION  <-  $BASE"
echo "  order: $UNITS"
echo

for unit in ${UNITS//,/ }; do
  echo "== $unit"
  while :; do
    rc=0; fetch_unit "$unit" || rc=$?
    [ "$rc" = 2 ] && { INCOMPLETE+=("$unit(error)"); break; }
    [ "$rc" = 0 ] && break
    if [ "$WATCH" = 1 ]; then
      echo "  [$unit] incomplete — repassing in ${POLL}s (Ctrl-C to stop)"
      sleep "$POLL"
    else
      INCOMPLETE+=("$unit"); break
    fi
  done
  echo
done

# Session-level manifest of record: every verified frame, one file, source hashes.
SM=$REPO/datasets/$SESSION/source_manifest.sha256
mkdir -p "$(dirname "$SM")"
: > "$SM"
for unit in ${UNITS//,/ }; do
  m=$REPO/datasets/$SESSION/$unit/ingest_work/$unit.sha256
  [ -f "$m" ] && awk -v u="$unit" '{print $1"  "u"/"$2}' "$m" >> "$SM"
done
sort -k2 -o "$SM" "$SM"

echo "fetch_session: verified OK=$GRAND_OK  BAD=$GRAND_BAD  moved=$(awk -v b=$GRAND_BYTES 'BEGIN{printf "%.1f", b/1073741824}') GiB"
echo "  manifest of record: ${SM#$REPO/} ($(wc -l < "$SM") frames)"
[ ${#INCOMPLETE[@]} -gt 0 ] && echo "  INCOMPLETE (rerun, or use --watch): ${INCOMPLETE[*]}"
[ "$GRAND_BAD" -eq 0 ] || exit 1
exit 0
