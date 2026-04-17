#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

echo "=============================================="
echo "   MUSEUM KIOSK - Dependency Installer"
echo "=============================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 not found."
  echo "Install Python 3.8 or higher and make sure it is available in PATH."
  exit 1
fi

echo "[INFO] Updating pip..."
python3 -m pip install --upgrade pip

echo "[INFO] Installing required packages from requirements.txt..."
python3 -m pip install -r requirements.txt

echo
echo "=============================================="
echo "[SUCCESS] Dependencies installed successfully."
echo
echo "You can now run the kiosk using:"
echo "  - ./launcher.sh"
echo "  - ./run_kiosk.sh"
echo "=============================================="
