#!/usr/bin/env bash
# run_daily.sh — fetch AI news, summarize, and email the digest.
#
# No pip install needed — pure Python stdlib only.
#
# Crontab setup (runs every day at 07:00 AM local time):
#   crontab -e
#   0 7 * * * /home/user/AI-Projects/ai-news-aggregator/run_daily.sh >> /home/user/AI-Projects/ai-news-aggregator/cron.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON="$(command -v python3)"

echo "=== AI Daily Digest — $(date '+%Y-%m-%d %H:%M %Z') ==="
"$PYTHON" "$SCRIPT_DIR/main.py"
echo "=== Done ==="
