#!/usr/bin/env bash
# Run the AI news digest. Loads .env, activates the venv, then calls main.py.
# Usage:
#   ./run_daily.sh             # fetch, summarize, and email
#   ./run_daily.sh --dry-run   # fetch and summarize only (no email sent)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load credentials from .env
if [ -f .env ]; then
    set -o allexport
    # shellcheck source=/dev/null
    source .env
    set +o allexport
else
    echo "ERROR: .env not found. Run setup.sh first."
    exit 1
fi

# Activate virtual environment
if [ ! -f .venv/bin/python ]; then
    echo "ERROR: Virtual environment not found. Run setup.sh first."
    exit 1
fi
source .venv/bin/activate

# Run the digest
python main.py "$@"
