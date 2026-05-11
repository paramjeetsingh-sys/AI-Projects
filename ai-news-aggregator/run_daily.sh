#!/usr/bin/env bash
# run_daily.sh — run the AI news digest and email it.
# Registered in crontab to run daily at 07:00 AM:
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

# Bootstrap virtualenv + dependencies on first run (or if venv is missing)
VENV="$SCRIPT_DIR/venv"
if [ ! -d "$VENV" ]; then
    echo "Creating virtualenv..."
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
    echo "Dependencies installed."
fi

PYTHON="$VENV/bin/python"

echo "=== AI Daily Digest — $(date '+%Y-%m-%d %H:%M %Z') ==="
"$PYTHON" "$SCRIPT_DIR/main.py"
echo "=== Done ==="
