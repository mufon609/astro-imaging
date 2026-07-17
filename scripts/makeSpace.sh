#!/usr/bin/env bash
# Reclaim VM file-transfer staging space — MANUAL-RUN utility.
#
# VMware stages every file dragged into the guest as a full copy under
# ~/.cache/vmware/drag_and_drop and never cleans it, so each raw-set transfer
# leaves a duplicate of the whole set on disk. Run this BY HAND after
# confirming the transferred files landed where they belong.
set -euo pipefail
du -sh ~/.cache/vmware/drag_and_drop 2>/dev/null || { echo "nothing staged"; exit 0; }
rm -rf ~/.cache/vmware/drag_and_drop
df -h / | tail -1
