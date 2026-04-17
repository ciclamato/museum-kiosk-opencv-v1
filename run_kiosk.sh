#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN="python3"
fi

echo "[INFO] Starting Museum Kiosk..."
echo

if ! "$PYTHON_BIN" main.py; then
  echo
  echo "[ERROR] Kiosk crashed or Python is not installed."
  exit 1
fi
