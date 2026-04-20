#!/bin/bash
# One-time setup script for AI Daily News Digest
# Run as root or with sudo for systemd steps

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== AI News Aggregator Setup ==="

# 1. Install Python dependencies
echo "[1/4] Installing Python dependencies..."
python3 -m venv "$SCRIPT_DIR/venv"
"$SCRIPT_DIR/venv/bin/pip" install --upgrade pip -q
"$SCRIPT_DIR/venv/bin/pip" install anthropic feedparser requests -q
echo "    Done."

# 2. Configure credentials
echo "[2/4] Credentials check..."
if grep -q "your_anthropic_api_key_here" "$SCRIPT_DIR/.env"; then
    echo "    [!] Please fill in your credentials in: $SCRIPT_DIR/.env"
    echo "        Required:"
    echo "          ANTHROPIC_API_KEY  → https://console.anthropic.com/"
    echo "          SMTP_USER          → your Gmail address"
    echo "          SMTP_PASSWORD      → Gmail App Password (not account password)"
    echo "        Then re-run this script."
    exit 1
fi
echo "    Credentials configured."

# 3. Install systemd units
echo "[3/4] Installing systemd timer (runs daily at 7:00 AM)..."
sudo cp "$SCRIPT_DIR/ai-digest.service" /etc/systemd/system/
sudo cp "$SCRIPT_DIR/ai-digest.timer" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ai-digest.timer
echo "    Timer enabled."

# 4. Test run (dry run)
echo "[4/4] Running a dry-run test..."
source "$SCRIPT_DIR/.env"
"$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/main.py" --dry-run

echo ""
echo "=== Setup complete! ==="
echo "The digest will be emailed to: $(grep RECIPIENT_EMAIL "$SCRIPT_DIR/.env" | cut -d= -f2)"
echo "Next run: $(systemctl show ai-digest.timer --property=NextElapseUSecRealtime 2>/dev/null | cut -d= -f2 || echo '7:00 AM tomorrow')"
echo ""
echo "Useful commands:"
echo "  Check timer:  systemctl status ai-digest.timer"
echo "  Run now:      systemctl start ai-digest.service"
echo "  View logs:    journalctl -u ai-digest.service -f"
