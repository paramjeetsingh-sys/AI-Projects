#!/usr/bin/env bash
# Daily AI news digest runner — sources .env then invokes main.py
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/digest_$(date +%Y-%m-%d).log"

mkdir -p "$SCRIPT_DIR/logs"

# Load environment variables from .env if present
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    set -o allexport
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/.env"
    set +o allexport
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting AI Daily Digest..." | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR"
python3 main.py "$@" 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Finished (exit $EXIT_CODE)." | tee -a "$LOG_FILE"
exit "$EXIT_CODE"
