#!/usr/bin/env bash
# Daily runner for the AI News Aggregator.
# Loads credentials from .env and invokes main.py.
# Designed to be called from cron (see setup_cron.sh).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
LOG_FILE="$SCRIPT_DIR/logs/digest.log"

# Load .env
if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] $ENV_FILE not found. Copy .env.example to .env and fill in your credentials." >&2
  exit 1
fi
set -a
# shellcheck source=/dev/null
source "$ENV_FILE"
set +a

# Ensure log directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Run with the venv python if it exists, otherwise fall back to system python3
if [[ -x "$SCRIPT_DIR/venv/bin/python3" ]]; then
  PYTHON="$SCRIPT_DIR/venv/bin/python3"
else
  PYTHON="python3"
fi

echo "=== $(date '+%Y-%m-%d %H:%M:%S') — Starting AI News Digest ===" >> "$LOG_FILE"
"$PYTHON" "$SCRIPT_DIR/main.py" 2>&1 | tee -a "$LOG_FILE"
echo "=== $(date '+%Y-%m-%d %H:%M:%S') — Done ===" >> "$LOG_FILE"
