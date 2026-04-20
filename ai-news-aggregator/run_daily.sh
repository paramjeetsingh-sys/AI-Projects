#!/bin/bash
# Daily AI News Digest runner
# Cron example (runs every day at 7:00 AM):
#   0 7 * * * /home/user/AI-Projects/ai-news-aggregator/run_daily.sh >> /var/log/ai-digest.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/ai-digest.log"

cd "$SCRIPT_DIR"

# Load env vars
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Activate virtualenv if present
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting AI Daily Digest..."
python3 "$SCRIPT_DIR/main.py"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Done."
