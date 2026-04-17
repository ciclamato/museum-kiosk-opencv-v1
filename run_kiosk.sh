#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

echo "[INFO] Starting Museum Kiosk..."
echo

if ! python3 main.py; then
  echo
  echo "[ERROR] Kiosk crashed or Python is not installed."
  exit 1
fi
