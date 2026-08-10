#!/usr/bin/env bash
# Watch the link to the remote publisher — reachability, latency, and progress.
#
#   link_heartbeat.sh [--host HOST:PORT] [--interval 10] [--log FILE] [--once]
#
# Answers the two questions a long overnight pull actually raises, which a
# transfer's own progress bar cannot:
#
#   IS THE LINK ALIVE?    ICMP rtt + HTTP status + fetch time for the index.
#                         A pull that has gone quiet is either a dead tunnel or
#                         a capture that simply has not written a new frame; the
#                         two look identical from inside the transfer.
#   IS THE SOURCE GROWING? Per-unit settled/pending counts from the publisher's
#                         index, differenced against the previous tick. A rising
#                         `settled` is the capture progressing; all-zero deltas
#                         with everything sealed means there is nothing left to
#                         wait for.
#
# Exits non-zero after --fail-after consecutive dead ticks, so it can gate a
# script rather than only inform a human.
#
# Writes JSONL to --log (default the session scratch under /tmp) — one object
# per tick, so a stall can be located in time after the fact instead of guessed.
set -euo pipefail

HOST=100.71.69.25:8000
INTERVAL=10 ONCE=0 FAIL_AFTER=6 LOG=""
for a in "$@"; do case "$a" in
  --host=*)        HOST=${a#*=};;
  --interval=*)    INTERVAL=${a#*=};;
  --log=*)         LOG=${a#*=};;
  --fail-after=*)  FAIL_AFTER=${a#*=};;
  --once)          ONCE=1;;
  *) echo "link_heartbeat: unknown arg $a" >&2; exit 2;;
esac; done

IP=${HOST%%:*}
BASE=http://$HOST
[ -n "$LOG" ] || LOG=${TMPDIR:-/tmp}/link_heartbeat_${IP//./_}.jsonl

printf '%-8s %-7s %-7s %-5s %s\n' TIME RTT_MS HTTP_MS CODE UNITS
dead=0
declare -A PREV=()

tick() {
  local t rtt code hms body
  t=$(date +%H:%M:%S)

  rtt=$(ping -c1 -W2 "$IP" 2>/dev/null | sed -n 's/.*time=\([0-9.]*\).*/\1/p' | head -1)
  [ -n "$rtt" ] || rtt=""

  body=$(curl -sS --connect-timeout 5 --max-time 20 \
           -w '\n%{http_code} %{time_total}' "$BASE/.publish/INDEX.json" 2>/dev/null || true)
  code=$(tail -1 <<<"$body" | cut -d' ' -f1)
  hms=$(tail -1 <<<"$body" | cut -d' ' -f2)
  hms=$(awk -v s="${hms:-0}" 'BEGIN{printf "%.0f", s*1000}')
  local json; json=$(sed '$d' <<<"$body")

  local summary="" alive=false
  if [ "${code:-000}" = "200" ]; then
    alive=true
    summary=$(python3 - <<PY 2>/dev/null || echo "(unparsable index)"
import json,sys
d=json.loads('''$json''')
print(" ".join(
  f"{u}:{v['settled']}{'+%d'%v['pending'] if v['pending'] else ''}{'*' if v['sealed'] else ''}"
  for u,v in d.get("units",{}).items()))
PY
)
  else
    summary="LINK DOWN (http=${code:-none})"
  fi

  printf '%-8s %-7s %-7s %-5s %s\n' "$t" "${rtt:--}" "$hms" "${code:-000}" "$summary"
  printf '{"epoch":%s,"rtt_ms":%s,"http_ms":%s,"http_code":"%s","alive":%s,"units":"%s"}\n' \
    "$(date +%s)" "${rtt:-null}" "$hms" "${code:-000}" "$alive" "$summary" >> "$LOG"

  [ "$alive" = true ]
}

while :; do
  if tick; then dead=0; else
    dead=$((dead + 1))
    if [ "$dead" -ge "$FAIL_AFTER" ]; then
      echo "link_heartbeat: link down for $dead consecutive ticks — giving up" >&2
      exit 1
    fi
  fi
  [ "$ONCE" = 1 ] && break
  sleep "$INTERVAL"
done
echo "link_heartbeat: log $LOG"
