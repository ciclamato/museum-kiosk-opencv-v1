#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

echo "=============================================="
echo "   MUSEUM KIOSK - Dependency Installer"
echo "=============================================="
echo

PYTHON_EXE=${PYTHON_EXE:-python3}

if ! command -v "$PYTHON_EXE" >/dev/null 2>&1; then
  echo "[ERROR] $PYTHON_EXE not found."
  echo "Please make sure Python 3.9 - 3.12 is installed and available in your PATH."
  exit 1
fi

# Check Python version
PY_VERSION=$("$PYTHON_EXE" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [ "$PY_VERSION" == "3.13" ]; then
  echo "[ERROR] Python 3.13 detected."
  echo "MediaPipe does not currently support Python 3.13 on Raspberry Pi / ARM64."
  echo "Please use Python 3.11 or 3.12 (standard in Raspberry Pi OS Bookworm)."
  echo "You can run this script with a specific version like this:"
  echo "  PYTHON_EXE=python3.11 ./install_requirements.sh"
  exit 1
fi

# Check Architecture
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ] && [ "$ARCH" != "x86_64" ]; then
  echo "[WARNING] Architecture $ARCH detected."
  echo "MediaPipe officially supports 64-bit systems (aarch64 or x86_64)."
  echo "If you are on a 32-bit OS, installation will likely fail."
fi

if [ ! -d ".venv" ]; then
  echo "[INFO] Creating local virtual environment in .venv..."
  if ! "$PYTHON_EXE" -m venv .venv; then
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
  echo "Common fixes for Raspberry Pi:"
  echo "1. Ensure you are using Python 3.11 or 3.12."
  echo "2. Install system dependencies:"
  echo "   sudo apt update && sudo apt install -y libgl1-mesa-glx libglib2.0-0 libusb-1.0-0"
  echo "3. Ensure you are on a 64-bit OS (run 'uname -m' should show 'aarch64')."
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
