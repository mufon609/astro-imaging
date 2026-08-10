#!/usr/bin/env bash
# Publish a capture directory for verified pull over HTTP — the REMOTE half.
#
#   remote_publish.sh <source-root> [--port 8000] [--bind 0.0.0.0]
#                     [--units darks,set-01,...] [--quiet-secs 30]
#                     [--interval 45] [--seal-secs 300] [--no-serve] [--once]
#
# Runs on the capture host. Two jobs, and nothing else:
#
#   1. HASH what has finished landing. Every settled file gets a sha256 in a
#      standard `sha256sum`-format manifest, one per unit, at
#      <root>/.publish/<unit>.sha256. The puller verifies against exactly this
#      file, so the integrity check is end-to-end: the hash is computed at the
#      source, never re-derived from the copy that is being checked.
#   2. SERVE the root over HTTP (python3 -m http.server) so the puller can GET
#      both the manifests and the frames.
#
# WHY A MANIFEST AND NOT A HASH-ON-DEMAND SERVICE. A static file server is the
# one thing a capture host can be relied on to run; anything richer is a service
# to debug at 3am with the sky clear. The manifest is a plain text file in the
# format coreutils `sha256sum -c` already consumes on the far side — no parser,
# no protocol, no in-house integrity scheme.
#
# WHY "SETTLED" IS THE WHOLE PROBLEM. Frames are published WHILE the camera is
# still writing. Hashing a file mid-write yields a hash of a partial file, the
# puller then fetches the finished file, and the mismatch reads as a corrupt
# transfer when nothing was corrupt. A file is published only when BOTH hold:
#   - its mtime is at least --quiet-secs old, and
#   - its size+mtime are unchanged when re-stat'd AFTER the hash completes.
# The second test is the load-bearing one: it closes the window where a file
# settles the age test and is then appended to during the hash itself. Anything
# failing either test is counted `pending` and reconsidered next cycle.
#
# A unit is `sealed` once it has no pending files and nothing has been written
# to it for --seal-secs. Sealed is the puller's only signal that a set is
# COMPLETE — file count alone cannot say, since a capture in progress and a
# finished capture look identical from the far side.
#
# Hashes are cached by name|size|mtime in <root>/.publish/.hashcache, so a
# re-scan costs a stat per file rather than a re-read of the whole set.
#
# The raw capture dirs are never written to — manifests, index and cache all
# live under <root>/.publish/.
set -euo pipefail

SRC=${1:?usage: remote_publish.sh <source-root> [options]}
shift || true
PORT=8000 BIND=0.0.0.0 QUIET=30 INTERVAL=45 SEAL=300 SERVE=1 ONCE=0 UNITS=""
for a in "$@"; do case "$a" in
  --port=*)       PORT=${a#*=};;
  --bind=*)       BIND=${a#*=};;
  --units=*)      UNITS=${a#*=};;
  --quiet-secs=*) QUIET=${a#*=};;
  --interval=*)   INTERVAL=${a#*=};;
  --seal-secs=*)  SEAL=${a#*=};;
  --no-serve)     SERVE=0;;
  --once)         ONCE=1;;
  *) echo "remote_publish: unknown arg $a" >&2; exit 2;;
esac; done

[ -d "$SRC" ] || { echo "remote_publish: no such dir: $SRC" >&2; exit 1; }
SRC=$(cd "$SRC" && pwd)
PUB=$SRC/.publish
mkdir -p "$PUB"

command -v sha256sum >/dev/null || { echo "remote_publish: sha256sum not found" >&2; exit 1; }
command -v python3   >/dev/null || [ "$SERVE" = 0 ] || {
  echo "remote_publish: python3 not found — rerun with --no-serve and start your own static server on $SRC" >&2; exit 1; }

RAW_EXT='nef|NEF|dng|DNG|cr2|CR2|cr3|CR3|arw|ARW|raf|RAF|fit|FIT|fits|FITS|jpg|JPG|jpeg|JPEG'

list_files() {  # <dir> -> "path<TAB>size<TAB>mtime" per regular raw file
  find "$1" -maxdepth 1 -type f -regextype posix-extended -regex ".*\.($RAW_EXT)$" -print0 2>/dev/null \
    | xargs -0 -r stat -c '%n	%s	%Y' 2>/dev/null || true
}

discover_units() {
  if [ -n "$UNITS" ]; then tr ',' '\n' <<<"$UNITS"; return; fi
  find "$SRC" -maxdepth 1 -mindepth 1 -type d -printf '%f\n' 2>/dev/null \
    | grep -Ev '^\.' | sort
}

declare -A CACHE=()
CACHEF=$PUB/.hashcache
if [ -f "$CACHEF" ]; then
  while IFS=$'\t' read -r k v; do [ -n "${k:-}" ] && CACHE[$k]=$v; done < "$CACHEF"
fi
save_cache() {
  local t=$PUB/.hashcache.tmp
  : > "$t"
  for k in "${!CACHE[@]}"; do printf '%s\t%s\n' "$k" "${CACHE[$k]}" >> "$t"; done
  mv -f "$t" "$CACHEF"
}

U_SETTLED=0 U_PENDING=0 U_BYTES=0 U_SEALED=false

publish_unit() {  # <unit> -> writes .publish/<unit>.sha256, sets U_* globals
  local unit=$1 dir=$SRC/$1
  local tmp=$PUB/.$unit.sha256.tmp out=$PUB/$unit.sha256
  local now path size mtime name key hash nsize nmtime newest=0
  now=$(date +%s)
  U_SETTLED=0 U_PENDING=0 U_BYTES=0 U_SEALED=false
  : > "$tmp"
  while IFS=$'\t' read -r path size mtime; do
    [ -n "${path:-}" ] || continue
    name=${path##*/}
    [ "$mtime" -gt "$newest" ] && newest=$mtime
    if [ $((now - mtime)) -lt "$QUIET" ]; then U_PENDING=$((U_PENDING + 1)); continue; fi
    key="$name|$size|$mtime"
    hash=${CACHE[$key]:-}
    if [ -z "$hash" ]; then
      hash=$(sha256sum "$path" | cut -d' ' -f1)
      # The file must be byte-identical to what was stat'd BEFORE the hash ran;
      # otherwise the hash describes a file that no longer exists.
      read -r nsize nmtime < <(stat -c '%s %Y' "$path" 2>/dev/null || echo "x x")
      if [ "$nsize" != "$size" ] || [ "$nmtime" != "$mtime" ]; then
        U_PENDING=$((U_PENDING + 1)); continue
      fi
      CACHE[$key]=$hash
    fi
    printf '%s  %s\n' "$hash" "$name" >> "$tmp"
    U_SETTLED=$((U_SETTLED + 1)); U_BYTES=$((U_BYTES + size))
  done < <(list_files "$dir")
  sort -k2 -o "$tmp" "$tmp"
  mv -f "$tmp" "$out"
  if [ "$U_PENDING" -eq 0 ] && [ "$U_SETTLED" -gt 0 ] && [ $((now - newest)) -ge "$SEAL" ]; then
    U_SEALED=true
  fi
}

write_index() {  # <units-json-body>
  local t=$PUB/.INDEX.json.tmp
  { printf '{\n "host": "%s",\n "root": "%s",\n' "$(hostname 2>/dev/null || echo unknown)" "$SRC"
    printf ' "heartbeat_epoch": %s,\n "quiet_secs": %s,\n "seal_secs": %s,\n' "$(date +%s)" "$QUIET" "$SEAL"
    printf ' "units": {\n%s\n }\n}\n' "$1"
  } > "$t"
  mv -f "$t" "$PUB/INDEX.json"
}

cycle() {
  local body="" unit first=1
  while read -r unit; do
    [ -n "${unit:-}" ] || continue
    [ -d "$SRC/$unit" ] || continue
    publish_unit "$unit"
    [ $first -eq 1 ] || body+=",\n"
    first=0
    body+=$(printf '  "%s": {"settled": %d, "pending": %d, "bytes": %d, "sealed": %s}' \
              "$unit" "$U_SETTLED" "$U_PENDING" "$U_BYTES" "$U_SEALED")
    printf '  %-12s settled=%-5d pending=%-4d %6.1f GiB  sealed=%s\n' \
      "$unit" "$U_SETTLED" "$U_PENDING" \
      "$(awk -v b="$U_BYTES" 'BEGIN{printf "%.1f", b/1073741824}')" "$U_SEALED"
  done < <(discover_units)
  save_cache
  write_index "$(printf '%b' "$body")"
}

SERVER_PID=""
cleanup() { [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

if [ "$SERVE" = 1 ]; then
  python3 -m http.server "$PORT" --bind "$BIND" --directory "$SRC" >/dev/null 2>&1 &
  SERVER_PID=$!
  sleep 1
  kill -0 "$SERVER_PID" 2>/dev/null || { echo "remote_publish: server failed to bind $BIND:$PORT" >&2; exit 1; }
  echo "remote_publish: serving $SRC on http://$BIND:$PORT/  (pid $SERVER_PID)"
fi
echo "remote_publish: root=$SRC quiet=${QUIET}s interval=${INTERVAL}s seal=${SEAL}s"

while :; do
  echo "-- scan $(date -Is)"
  cycle
  [ "$ONCE" = 1 ] && break
  sleep "$INTERVAL"
done

if [ "$SERVE" = 1 ] && [ "$ONCE" = 1 ]; then
  echo "remote_publish: --once with --serve; server stays up, Ctrl-C to stop"
  wait "$SERVER_PID"
fi
