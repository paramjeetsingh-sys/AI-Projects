#!/usr/bin/env bash
# One-time setup: install deps, create .env, and register the daily cron job.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(command -v python3)"
RUN_SCRIPT="$SCRIPT_DIR/run.sh"

echo "=== AI News Aggregator — Setup ==="

# 1. Install Python dependencies
echo "[1/3] Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet

# 2. Create .env from example if it doesn't exist
if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo ""
    echo "  ✦ Created .env — FILL IN your credentials before running:"
    echo "    $SCRIPT_DIR/.env"
    echo ""
else
    echo "[2/3] .env already exists — skipping."
fi

# 3. Make run script executable
chmod +x "$RUN_SCRIPT"

# 4. Register daily cron job (08:00 AM local time)
CRON_CMD="0 8 * * * $RUN_SCRIPT >> $SCRIPT_DIR/logs/cron.log 2>&1"
(crontab -l 2>/dev/null | grep -qF "$RUN_SCRIPT") && {
    echo "[3/3] Cron job already registered — no change."
} || {
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "[3/3] Cron job registered: runs daily at 08:00 AM."
    echo "      $CRON_CMD"
}

echo ""
echo "=== Setup complete ==="
echo "  Edit credentials : $SCRIPT_DIR/.env"
echo "  Run manually     : $RUN_SCRIPT"
echo "  Dry run          : $RUN_SCRIPT --dry-run"
echo "  View logs        : $SCRIPT_DIR/logs/"
echo ""
