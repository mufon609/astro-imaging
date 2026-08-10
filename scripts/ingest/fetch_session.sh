#!/usr/bin/env bash
# Pull a capture session from the remote host, verified — the LOCAL half.
#
#   fetch_session.sh <session> [--host HOST:PORT] [--units dark,set-01,...]
#                    [--dest DIR] [--watch] [--retries 3] [--dry-run]
#                    [--settle-secs 60] [--require-manifest]
#
# TWO INTEGRITY LEVELS, chosen by what the remote is actually running.
#
#   SOURCE-VERIFIED (full) — scripts/ingest/remote_publish.sh is running there.
#     It hashes each settled frame AT THE SOURCE into a `sha256sum`-format
#     manifest per unit. This side fetches the manifest, then the frames, then
#     checks the landed copies with coreutils `sha256sum -c`. The comparison is
#     source-computed hash vs destination-computed hash, which is the only form
#     that proves anything: re-hashing the copy on both ends only proves the
#     copy equals itself.
#
#   TRANSFER-VERIFIED (fallback) — the remote is a plain `python3 -m
#     http.server` with no publisher. There is no source hash to compare
#     against, so this mode verifies what HTTP alone can prove: the unit is
#     enumerated from the directory listing, each file's Content-Length and
#     Last-Modified are read by HEAD, the landed file must match Content-Length
#     exactly, and a re-HEAD after the transfer must show size and Last-Modified
#     unchanged. That catches truncation, a short read, and a file rewritten
#     mid-download — but NOT silent bit corruption, which only a source hash can
#     catch. Every such frame is hashed locally into <unit>.local.sha256 and the
#     record says `integrity: transfer-verified`, never source-verified.
#
#     THE FALLBACK IS AN UPGRADE PATH, NOT A DEAD END. Start the publisher later
#     and re-run: every already-landed frame is hashed and compared to the
#     source manifest, so the whole set becomes source-verified with no
#     re-download of anything that matches. Pull now, prove it properly later.
#
# THE "STILL BEING WRITTEN" PROBLEM applies in both modes and is the reason a
# naive pull corrupts data. A static server serves a half-written file happily,
# with a Content-Length describing the half. The publisher solves this with a
# post-hash re-stat; the fallback solves it from HTTP metadata, skipping any
# file whose Last-Modified is newer than --settle-secs against the server's own
# Date header (both from the same response, so clock skew cannot mis-age it).
#
# A frame is moved into place only after its own check passes, so the
# destination never contains an unverified frame — an interrupted run leaves
# .part files, never a corrupt NEF that a later pass would trust. Re-running is
# the normal mode of operation while a capture is in progress.
#
# DESTINATION. Default is the repo session tree sessions/<session>/<unit>/, with
# records under datasets/<session>/<unit>/ingest_work/. --dest DIR puts frames
# in DIR/<unit>/ and records in DIR/_ingest/, touching no repo path at all —
# for staging a night outside the repo.
set -euo pipefail
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && cd .. && pwd)

SESSION=${1:?usage: fetch_session.sh <session> [--host HOST:PORT] [--units a,b] [--dest DIR] [--watch]}
shift || true
HOST=100.71.69.25:8000
UNITS="dark,set-01,set-02,set-03,set-04,set-05"
RETRIES=3 WATCH=0 DRY=0 POLL=60 SETTLE=60 DEST="" REQMAN=0
for a in "$@"; do case "$a" in
  --host=*)         HOST=${a#*=};;
  --units=*)        UNITS=${a#*=};;
  --dest=*)         DEST=${a#*=};;
  --retries=*)      RETRIES=${a#*=};;
  --poll=*)         POLL=${a#*=};;
  --settle-secs=*)  SETTLE=${a#*=};;
  --require-manifest) REQMAN=1;;
  --watch)          WATCH=1;;
  --dry-run)        DRY=1;;
  *) echo "fetch_session: unknown arg $a" >&2; exit 2;;
esac; done

if [ -n "$DEST" ]; then
  mkdir -p "$DEST"; DEST=$(cd "$DEST" && pwd)
  FRAME_ROOT=$DEST; REC_ROOT=$DEST/_ingest; MANIFEST_OF_RECORD=$DEST/source_manifest.sha256
else
  FRAME_ROOT=$REPO/sessions/$SESSION; REC_ROOT=$REPO/datasets/$SESSION
  MANIFEST_OF_RECORD=$REPO/datasets/$SESSION/source_manifest.sha256
fi

BASE=http://$HOST
CURL=(curl -fsS --connect-timeout 10 --max-time 900 --retry 2 --retry-delay 3)

if ! "${CURL[@]}" -o /dev/null "$BASE/"; then
  cat >&2 <<EOF
fetch_session: nothing serving at $BASE

  On the capture host:  remote_publish.sh <capture-root> --port ${HOST##*:}
  (host reachable? try: ping -c2 ${HOST%%:*})
EOF
  exit 1
fi

MODE=fallback
if "${CURL[@]}" -o /dev/null "$BASE/.publish/INDEX.json" 2>/dev/null; then MODE=publisher; fi
if [ "$MODE" = fallback ] && [ "$REQMAN" = 1 ]; then
  echo "fetch_session: --require-manifest given but no publisher at $BASE/.publish/" >&2; exit 1
fi

GRAND_OK=0 GRAND_BAD=0 GRAND_BYTES=0 INCOMPLETE=()
SAFE_NAME='^[A-Za-z0-9._-]+$'

http_date_epoch() { date -d "$1" +%s 2>/dev/null || echo 0; }

# ---- one file: fetch to .part, check, move -----------------------------------
# Resume is worth one attempt on a big frame over a slow link, but must not be
# able to loop: a .part already at full length makes the server answer 416 to
# every further ranged request, and a .part whose bytes are wrong can never hash
# correctly however much is appended. So a failed or non-verifying resume drops
# the part and the next try starts clean.
DL_BYTES=0
fetch_one() {  # <url> <part> <target> <expect-hash|""> <expect-size|"">
  local url=$1 part=$2 target=$3 want_hash=$4 want_size=$5
  local try=0
  while [ $try -lt "$RETRIES" ]; do
    try=$((try + 1))
    local resume=(); [ -f "$part" ] && resume=(-C -)
    if "${CURL[@]}" "${resume[@]}" -o "$part" "$url"; then
      local got_size; got_size=$(stat -c '%s' "$part" 2>/dev/null || echo -1)
      local ok=1
      [ -n "$want_size" ] && [ "$got_size" != "$want_size" ] && ok=0
      if [ -n "$want_hash" ] && [ "$(sha256sum "$part" | cut -d' ' -f1)" != "$want_hash" ]; then ok=0; fi
      if [ $ok -eq 1 ]; then
        DL_BYTES=$got_size; mv -f "$part" "$target"; return 0
      fi
      rm -f "$part"
    elif [ $try -ge 2 ]; then
      rm -f "$part"
    fi
    sleep 2
  done
  return 1
}

# ---- publisher mode ----------------------------------------------------------
unit_sealed() {
  "${CURL[@]}" "$BASE/.publish/INDEX.json" \
    | python3 -c 'import json,sys;print(json.load(sys.stdin)["units"].get(sys.argv[1],{}).get("sealed",False))' "$1" 2>/dev/null
}

fetch_unit_publisher() {  # <unit> -> 0 complete, 1 incomplete, 2 error
  local unit=$1 dest=$FRAME_ROOT/$1 work=$REC_ROOT/$1/ingest_work
  [ -n "$DEST" ] && work=$REC_ROOT/$1
  local man=$work/$unit.sha256
  mkdir -p "$dest" "$work"

  if ! "${CURL[@]}" -o "$man.tmp" "$BASE/.publish/$unit.sha256"; then
    echo "  [$unit] no manifest published yet"; rm -f "$man.tmp"; return 1
  fi
  mv -f "$man.tmp" "$man"
  local total; total=$(wc -l < "$man")
  [ "$total" -eq 0 ] && { echo "  [$unit] manifest empty — nothing settled yet"; return 1; }
  if grep -qE '^[0-9a-f]{64}  .*[^A-Za-z0-9._-]' "$man"; then
    echo "  [$unit] manifest has names needing URL escaping — refusing" >&2; return 2
  fi

  local got=0 skip=0 bad=0 bytes=0 n=0 t0 hash name
  t0=$(date +%s)
  # sha256sum format is "<hash><space><space><name>"; the charset guard above
  # is what makes a plain two-field read safe here.
  while read -r hash name; do
    n=$((n + 1))
    local target=$dest/$name part=$dest/.$name.part
    if [ -f "$target" ] && [ "$(sha256sum "$target" | cut -d' ' -f1)" = "$hash" ]; then
      skip=$((skip + 1)); continue
    fi
    [ "$DRY" = 1 ] && { got=$((got + 1)); continue; }
    if fetch_one "$BASE/$unit/$name" "$part" "$target" "$hash" ""; then
      bytes=$((bytes + DL_BYTES)); got=$((got + 1))
    else
      echo "  [$unit] FAILED after $RETRIES tries: $name" >&2; bad=$((bad + 1))
    fi
    progress "$unit" "$n" "$total" "$got" "$skip" "$bad" "$bytes" "$t0"
  done < "$man"

  local report=$work/verify.txt rc=0
  ( cd "$dest" && sha256sum -c "$man" ) > "$report" 2>&1 || rc=$?
  local vok vbad
  vok=$(grep -c ': OK$' "$report" || true)
  vbad=$(grep -cE ': (FAILED|FAILED open or read)$' "$report" || true)
  local sealed; sealed=$(unit_sealed "$unit")

  write_record "$work/ingest.json" "$unit" source-verified "$total" "$got" "$skip" "$bad" \
               "$vok" "$vbad" "$rc" "$bytes" "$(( $(date +%s) - t0 ))" "$sealed"
  printf '  [%s] entries=%d new=%d had=%d fail=%d  verify: OK=%d BAD=%d  sealed=%s\n' \
    "$unit" "$total" "$got" "$skip" "$bad" "$vok" "$vbad" "$sealed"
  GRAND_OK=$((GRAND_OK + vok)); GRAND_BAD=$((GRAND_BAD + vbad + bad)); GRAND_BYTES=$((GRAND_BYTES + bytes))
  [ "$vbad" -eq 0 ] && [ "$bad" -eq 0 ] && [ "${sealed,,}" = "true" ] && return 0
  return 1
}

# ---- fallback mode -----------------------------------------------------------
list_unit() {  # <unit> -> filenames from the directory listing
  "${CURL[@]}" "$BASE/$1/" 2>/dev/null \
    | grep -oE 'href="[^"?]+"' | sed 's/^href="//; s/"$//' \
    | grep -viE '/$' \
    | grep -iE '\.(nef|dng|cr2|cr3|arw|raf|fits?|jpe?g)$' | sort -u
}

fetch_unit_listing() {  # <unit> -> 0 quiesced+verified, 1 incomplete, 2 error
  local unit=$1 dest=$FRAME_ROOT/$1 work=$REC_ROOT/$1/ingest_work
  [ -n "$DEST" ] && work=$REC_ROOT/$1
  mkdir -p "$dest" "$work"

  local names; names=$(list_unit "$unit") || true
  [ -n "$names" ] || { echo "  [$unit] not present on the remote yet"; return 1; }
  local total; total=$(wc -l <<<"$names")

  local got=0 skip=0 bad=0 pending=0 bytes=0 n=0 t0 name
  t0=$(date +%s)
  local lman=$work/$unit.local.sha256; : > "$lman.tmp"

  while read -r name; do
    n=$((n + 1))
    [[ $name =~ $SAFE_NAME ]] || { echo "  [$unit] unsafe name, skipped: $name" >&2; bad=$((bad+1)); continue; }
    local target=$dest/$name part=$dest/.$name.part

    local head; head=$("${CURL[@]}" -I "$BASE/$unit/$name" 2>/dev/null) || { pending=$((pending+1)); continue; }
    local size lm srv
    size=$(grep -i '^content-length:'  <<<"$head" | tr -d '\r' | awk '{print $2}')
    lm=$(  grep -i '^last-modified:'   <<<"$head" | tr -d '\r' | cut -d' ' -f2-)
    srv=$( grep -i '^date:'            <<<"$head" | tr -d '\r' | cut -d' ' -f2-)
    [ -n "$size" ] || { pending=$((pending+1)); continue; }

    # Settled? Age the file against the SERVER's own clock, from this same
    # response — a client-clock comparison would mis-age every file by the skew.
    local age=$(( $(http_date_epoch "$srv") - $(http_date_epoch "$lm") ))
    if [ "$age" -lt "$SETTLE" ]; then pending=$((pending + 1)); continue; fi

    if [ -f "$target" ] && [ "$(stat -c '%s' "$target")" = "$size" ]; then
      skip=$((skip + 1))
      printf '%s  %s\n' "$(sha256sum "$target" | cut -d' ' -f1)" "$name" >> "$lman.tmp"
      continue
    fi
    [ "$DRY" = 1 ] && { got=$((got + 1)); continue; }

    if fetch_one "$BASE/$unit/$name" "$part" "$target" "" "$size"; then
      # The file must not have been rewritten underneath the transfer.
      local h2 lm2 sz2
      h2=$("${CURL[@]}" -I "$BASE/$unit/$name" 2>/dev/null || true)
      sz2=$(grep -i '^content-length:' <<<"$h2" | tr -d '\r' | awk '{print $2}')
      lm2=$(grep -i '^last-modified:'  <<<"$h2" | tr -d '\r' | cut -d' ' -f2-)
      if [ "$sz2" != "$size" ] || [ "$lm2" != "$lm" ]; then
        echo "  [$unit] changed during transfer, will retry next pass: $name" >&2
        rm -f "$target"; pending=$((pending + 1)); continue
      fi
      bytes=$((bytes + DL_BYTES)); got=$((got + 1))
      printf '%s  %s\n' "$(sha256sum "$target" | cut -d' ' -f1)" "$name" >> "$lman.tmp"
    else
      echo "  [$unit] FAILED after $RETRIES tries: $name" >&2; bad=$((bad + 1))
    fi
    progress "$unit" "$n" "$total" "$got" "$skip" "$bad" "$bytes" "$t0"
  done <<<"$names"

  sort -k2 -o "$lman.tmp" "$lman.tmp"; mv -f "$lman.tmp" "$lman"
  local landed; landed=$(wc -l < "$lman")

  write_record "$work/ingest.json" "$unit" transfer-verified "$total" "$got" "$skip" "$bad" \
               "$landed" 0 0 "$bytes" "$(( $(date +%s) - t0 ))" "$([ "$pending" -eq 0 ] && echo true || echo false)" "$pending"
  printf '  [%s] listed=%d new=%d had=%d fail=%d in-flight=%d  landed+hashed=%d\n' \
    "$unit" "$total" "$got" "$skip" "$bad" "$pending" "$landed"
  GRAND_OK=$((GRAND_OK + landed)); GRAND_BAD=$((GRAND_BAD + bad)); GRAND_BYTES=$((GRAND_BYTES + bytes))
  [ "$bad" -eq 0 ] && [ "$pending" -eq 0 ] && return 0
  return 1
}

progress() {  # <unit> n total got skip bad bytes t0
  [ $(( $2 % 25 )) -eq 0 ] || return 0
  local el=$(( $(date +%s) - $8 )); [ "$el" -eq 0 ] && el=1
  printf '  [%s] %d/%d  new=%d have=%d fail=%d  %s MiB/s\n' "$1" "$2" "$3" "$4" "$5" "$6" \
    "$(awk -v b="$7" -v e="$el" 'BEGIN{printf "%.1f", b/1048576/e}')"
}

write_record() {  # path unit integrity total got skip bad ok bad2 rc bytes secs sealed [pending]
  SESSION="$SESSION" HOSTP="$HOST" python3 - "$@" <<'PY'
import json, os, sys
(p, unit, integrity, total, got, skip, bad, vok, vbad, rc, byts, el, sealed) = sys.argv[1:14]
pending = int(sys.argv[14]) if len(sys.argv) > 14 else 0
sealed_b = str(sealed).strip().lower() == "true"
rec = {
  "session": os.environ["SESSION"], "unit": unit,
  "source": f"http://{os.environ['HOSTP']}/{unit}",
  "integrity": integrity,
  "remote_entries": int(total), "downloaded": int(got), "already_present": int(skip),
  "download_failed": int(bad), "in_flight_skipped": pending,
  "verified_ok": int(vok), "verified_bad": int(vbad), "verify_exit": int(rc),
  "bytes_transferred": int(byts), "seconds": int(el),
  "mib_per_s": round(int(byts)/1048576/max(int(el),1), 2),
  "remote_quiesced": sealed_b,
  "complete": sealed_b and int(vbad) == 0 and int(bad) == 0,
}
rec["_note"] = (
  "source-verified: hashes computed at the source by remote_publish.sh and checked "
  "here with sha256sum -c. transfer-verified: no publisher was running, so "
  "completeness was proven from Content-Length plus an unchanged Last-Modified "
  "across the transfer, and the sha256 in <unit>.local.sha256 is a DESTINATION "
  "hash — re-run against a running publisher to upgrade it to source-verified."
)
json.dump(rec, open(p, "w"), indent=1)
PY
}

# ---- drive -------------------------------------------------------------------
echo "fetch_session: $SESSION  <-  $BASE"
echo "  mode:   $MODE  ($([ "$MODE" = publisher ] && echo 'source-verified' || echo 'transfer-verified — no publisher on the remote'))"
echo "  order:  $UNITS"
echo "  frames: $FRAME_ROOT"
echo "  records:$REC_ROOT"
echo

for unit in ${UNITS//,/ }; do
  echo "== $unit"
  while :; do
    rc=0
    if [ "$MODE" = publisher ]; then fetch_unit_publisher "$unit" || rc=$?
    else                            fetch_unit_listing   "$unit" || rc=$?; fi
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

# Rebuilt from EVERY unit recorded under REC_ROOT, not just this run's --units:
# running disjoint units as concurrent processes is the normal way to use a
# saturated uplink, and a run that emitted only its own units would truncate the
# session manifest to whichever process happened to finish last.
mkdir -p "$(dirname "$MANIFEST_OF_RECORD")"
tmp_mor=$MANIFEST_OF_RECORD.$$
: > "$tmp_mor"
while read -r w; do
  [ -n "$w" ] || continue
  u=$(basename "$(dirname "$w")")
  [ "$(basename "$w")" = ingest_work ] || u=$(basename "$w")
  for m in "$w/$u.sha256" "$w/$u.local.sha256"; do
    [ -f "$m" ] && { awk -v u="$u" '{print $1"  "u"/"$2}' "$m" >> "$tmp_mor"; break; }
  done
done < <(find "$REC_ROOT" -maxdepth 2 -type d \( -name ingest_work -o -name 'set-*' -o -name 'dark*' \) 2>/dev/null | sort -u)
sort -u -k2 -o "$tmp_mor" "$tmp_mor"
mv -f "$tmp_mor" "$MANIFEST_OF_RECORD"

echo "fetch_session: frames verified=$GRAND_OK  bad=$GRAND_BAD  moved=$(awk -v b=$GRAND_BYTES 'BEGIN{printf "%.1f", b/1073741824}') GiB"
echo "  manifest of record: $MANIFEST_OF_RECORD ($(wc -l < "$MANIFEST_OF_RECORD") frames)"
[ ${#INCOMPLETE[@]} -gt 0 ] && echo "  INCOMPLETE (rerun, or use --watch): ${INCOMPLETE[*]}"
[ "$GRAND_BAD" -eq 0 ] || exit 1
exit 0
