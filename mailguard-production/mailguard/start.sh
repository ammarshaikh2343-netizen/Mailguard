#!/usr/bin/env bash
echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║   MailGuard — Email DNS Checker      ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

command -v python3 &>/dev/null || { echo "[ERROR] Python3 required."; exit 1; }

echo "[1/2] Installing dependencies..."
pip3 install -r requirements.txt --quiet --break-system-packages 2>/dev/null || \
pip3 install -r requirements.txt --quiet

echo "[2/2] Starting MailGuard on http://localhost:5050"
echo "  Open: http://localhost:5050  |  Stop: Ctrl+C"
echo ""

(sleep 2 && (open "http://localhost:5050" 2>/dev/null || xdg-open "http://localhost:5050" 2>/dev/null)) &
python3 app.py
