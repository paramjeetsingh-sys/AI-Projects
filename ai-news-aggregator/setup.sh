#!/usr/bin/env bash
# One-time setup: create venv and install dependencies.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== AI News Aggregator — Setup ==="

# Require .env
if [ ! -f .env ]; then
    echo "ERROR: .env not found."
    echo "Run: cp .env.template .env  and fill in your credentials."
    exit 1
fi

# Create virtual environment if needed
if [ ! -d .venv ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Install dependencies
echo "Installing Python dependencies..."
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

echo ""
echo "Setup complete!"
echo "Test it now with:  ./run_daily.sh --dry-run"
echo "Add daily cron:    ./install_cron.sh"
