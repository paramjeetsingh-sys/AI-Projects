#!/usr/bin/env bash
# run_daily.sh — run the AI news digest and email it.
# Add to crontab with:  crontab -e
# Example (runs every day at 07:00 AM):
#   0 7 * * * /home/user/AI-Projects/ai-news-aggregator/run_daily.sh >> /home/user/AI-Projects/ai-news-aggregator/cron.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Load .env if present (cron has a minimal environment)
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Use virtualenv if it exists next to the project (.venv preferred, venv as fallback)
if [ -d "$SCRIPT_DIR/.venv" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif [ -d "$SCRIPT_DIR/venv" ]; then
    PYTHON="$SCRIPT_DIR/venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

echo "=== AI Daily Digest — $(date '+%Y-%m-%d %H:%M %Z') ==="
"$PYTHON" "$SCRIPT_DIR/main.py"
echo "=== Done ==="
