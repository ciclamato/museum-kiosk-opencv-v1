#!/usr/bin/env bash
# ==============================================================================
# Museum Kiosk — Miniforge Environment Installer for Raspberry Pi
# ==============================================================================
# Sets up a optimized Conda environment for MediaPipe on ARM64.
# ==============================================================================

set -u
cd "$(dirname "$0")"

ENVIRONMENT_NAME="kiosk"
PYTHON_VERSION="3.11" # 3.11 is the most stable for MediaPipe on Pi

echo "--- Museum Kiosk: Miniforge Setup ---"

# 1. Check for Conda
if ! command -v conda >/dev/null 2>&1; then
    echo "[ERROR] Conda not found. Please install Miniforge first:"
    echo "wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh"
    echo "bash Miniforge3-Linux-aarch64.sh"
    exit 1
fi

# 2. Create/Update Environment
echo "[INFO] Creating/Updating conda environment '$ENVIRONMENT_NAME' with Python $PYTHON_VERSION..."
conda create -y -n "$ENVIRONMENT_NAME" python="$PYTHON_VERSION"

# 3. Install Dependencies
echo "[INFO] Installing dependencies via pip inside conda..."
conda run -n "$ENVIRONMENT_NAME" pip install --upgrade pip
conda run -n "$ENVIRONMENT_NAME" pip install -r requirements.txt

# 4. Success
echo "------------------------------------------------"
echo "[SUCCESS] Environment '$ENVIRONMENT_NAME' is ready."
echo "You can now use './launch_kiosk_pi.sh' to start."
echo "------------------------------------------------"
