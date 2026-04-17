#!/usr/bin/env bash
# Installs (or updates) the daily cron job for the AI News Digest.
# Run once:  bash setup_cron.sh [HH:MM]   (default: 07:00 local time)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="$SCRIPT_DIR/run_daily.sh"
TIME="${1:-07:00}"
HOUR="${TIME%%:*}"
MINUTE="${TIME##*:}"

chmod +x "$RUNNER"

# Remove any previous entry for this runner, then add the new one
( crontab -l 2>/dev/null | grep -v "$RUNNER" ; \
  echo "$MINUTE $HOUR * * * $RUNNER" ) | crontab -

echo "Cron job installed: runs every day at ${HOUR}:${MINUTE} local time."
echo "Current crontab:"
crontab -l | grep "$RUNNER"
