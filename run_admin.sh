#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

echo "[INFO] Starting Museum Kiosk Admin Panel..."
echo "[INFO] Once running, open http://localhost:5000 in your browser."
echo

if ! "$PYTHON_BIN" main.py --admin; then
  echo
  echo "[ERROR] Admin panel failed to start. Ensure Python is installed."
  exit 1
fi
