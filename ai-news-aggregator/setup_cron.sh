#!/usr/bin/env bash
# Installs (or removes) the daily cron job for the AI News Aggregator.
# Requires root — uses /etc/cron.d which works on systems without per-user crontabs.
#
#   Install: sudo bash setup_cron.sh
#   Remove:  sudo bash setup_cron.sh --remove

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_FILE="/etc/cron.d/ai-news-digest"

if [[ "${1:-}" == "--remove" ]]; then
  rm -f "$CRON_FILE"
  echo "Cron job removed ($CRON_FILE deleted)."
  exit 0
fi

chmod +x "$SCRIPT_DIR/run_daily.sh"
mkdir -p "$SCRIPT_DIR/logs"

cat > "$CRON_FILE" <<EOF
# AI News Aggregator — Daily Digest
# Runs every day at 08:00 AM UTC and emails the digest.
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

0 8 * * * root $SCRIPT_DIR/run_daily.sh >> $SCRIPT_DIR/logs/cron.log 2>&1
EOF

chmod 644 "$CRON_FILE"
echo "Cron job installed at $CRON_FILE"
echo "Digest will run daily at 08:00 AM UTC."
echo ""
cat "$CRON_FILE"
