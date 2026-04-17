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

if [ ! -d ".venv" ]; then
  echo "[INFO] Creating local virtual environment in .venv..."
  if ! python3 -m venv .venv; then
    echo "[ERROR] Could not create the virtual environment."
    echo "On Raspberry Pi OS, install it with:"
    echo "  sudo apt install python3-venv python3-full"
    exit 1
  fi
fi

PYTHON_BIN=".venv/bin/python"
PIP_BIN=".venv/bin/pip"

echo "[INFO] Updating pip inside .venv..."
"$PYTHON_BIN" -m pip install --upgrade pip

echo "[INFO] Installing required packages from requirements.txt..."
if ! "$PIP_BIN" install -r requirements.txt; then
  echo
  echo "[ERROR] Installation failed inside .venv."
  echo "If a package needs system libraries on Raspberry Pi, install them with apt first."
  exit 1
fi

echo
echo "=============================================="
echo "[SUCCESS] Dependencies installed successfully."
echo
echo "You can now run the kiosk using:"
echo "  - ./launcher.sh"
echo "  - ./run_kiosk.sh"
echo
echo "This project now uses the local virtual environment:"
echo "  ./.venv"
echo "=============================================="
