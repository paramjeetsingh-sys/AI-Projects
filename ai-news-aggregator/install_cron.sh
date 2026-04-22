#!/usr/bin/env bash
# Installs (or updates) a daily cron job that runs the AI news digest at 7:00 AM.
# Edit CRON_HOUR / CRON_MINUTE below to change the schedule.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_daily.sh"
LOG_FILE="$SCRIPT_DIR/digest.log"

CRON_MINUTE=0
CRON_HOUR=7   # 7 AM server local time — change to match your timezone

CRON_LINE="$CRON_MINUTE $CRON_HOUR * * * $RUN_SCRIPT >> $LOG_FILE 2>&1"
CRON_MARKER="# ai-news-aggregator"

# Remove any existing ai-news-aggregator cron entry, then add the new one
(crontab -l 2>/dev/null | grep -v "$CRON_MARKER"; echo "$CRON_LINE $CRON_MARKER") | crontab -

echo "Cron job installed:"
echo "  $CRON_LINE"
echo ""
echo "Logs will be written to: $LOG_FILE"
echo ""
echo "Current crontab:"
crontab -l
