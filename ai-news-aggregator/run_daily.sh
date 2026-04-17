#!/usr/bin/env bash
# Daily AI News Digest runner — invoked by cron

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
LOG_FILE="$SCRIPT_DIR/logs/digest.log"

# Load .env if present
if [[ -f "$ENV_FILE" ]]; then
    set -o allexport
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +o allexport
fi

mkdir -p "$SCRIPT_DIR/logs"

# Rotate: keep last 30 log files
find "$SCRIPT_DIR/logs" -name "digest-*.log" | sort | head -n -30 | xargs -r rm --

DATED_LOG="$SCRIPT_DIR/logs/digest-$(date +%Y%m%d).log"

{
    echo "=== AI News Digest run: $(date -u '+%Y-%m-%d %H:%M UTC') ==="
    cd "$SCRIPT_DIR"

    # Use virtual-env python if available, else system python3
    PYTHON="${SCRIPT_DIR}/.venv/bin/python"
    [[ -x "$PYTHON" ]] || PYTHON="$(command -v python3)"

    "$PYTHON" main.py
    echo "=== Run complete ==="
} 2>&1 | tee "$DATED_LOG"
