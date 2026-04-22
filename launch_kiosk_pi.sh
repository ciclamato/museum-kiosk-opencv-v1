#!/usr/bin/env bash
# ==============================================================================
# Museum Kiosk — Raspberry Pi Optimized Launcher (Miniforge/Conda)
# ==============================================================================
# This script ensures the kiosk is always running, handles conda activation,
# and waits for system resources to be ready.
# ==============================================================================

set -u
cd "$(dirname "$0")"

ENVIRONMENT_NAME="kiosk" # Change this to your conda environment name
LOG_FILE="kiosk_launch.log"

echo "[$(date)] --- Launching Museum Kiosk ---" | tee -a "$LOG_FILE"

# 1. Locate Conda/Miniforge
# Common installation paths for Miniforge
CONDA_PATHS=(
    "$HOME/miniforge3/bin/conda"
    "$HOME/mambaforge/bin/conda"
    "$HOME/anaconda3/bin/conda"
    "$HOME/miniconda3/bin/conda"
    "/opt/miniforge3/bin/conda"
)

CONDA_EXE=""
for path in "${CONDA_PATHS[@]}"; do
    if [ -x "$path" ]; then
        CONDA_EXE="$path"
        break
    fi
done

if [ -z "$CONDA_EXE" ]; then
    # Last ditch effort: is it in PATH?
    if command -v conda >/dev/null 2>&1; then
        CONDA_EXE=$(command -v conda)
    else
        echo "[ERROR] Conda/Miniforge not found. Please install it or check path." | tee -a "$LOG_FILE"
        exit 1
    fi
fi

echo "[INFO] Using Conda at: $CONDA_EXE"

# 2. Activate Environment
# We need to evaluate the conda shell hook to use 'conda activate'
CONDA_BASE=$(dirname "$(dirname "$CONDA_EXE")")
source "$CONDA_BASE/etc/profile.d/conda.sh"

if ! conda activate "$ENVIRONMENT_NAME" 2>/dev/null; then
    echo "[WARNING] Could not activate environment '$ENVIRONMENT_NAME'." | tee -a "$LOG_FILE"
    echo "[INFO] Attempting to use local .venv as fallback..." | tee -a "$LOG_FILE"
    if [ -d ".venv" ]; then
        PYTHON_BIN=".venv/bin/python"
    else
        PYTHON_BIN="python3"
    fi
else
    echo "[INFO] Environment '$ENVIRONMENT_NAME' activated." | tee -a "$LOG_FILE"
    PYTHON_BIN="python"
fi

# 3. Wait for Hardware (Optional - helps on boot)
echo "[INFO] Waiting 5s for camera and system resources..."
sleep 5

# 4. Infinite Loop (Auto-Restart on Crash)
RESTART_COUNT=0
while true; do
    echo "[$(date)] Starting Kiosk (Attempt $((++RESTART_COUNT)))..." | tee -a "$LOG_FILE"
    
    # Run the kiosk with default Spanish language
    # Adjust args as needed (e.g., --debug or --camera 1)
    "$PYTHON_BIN" main.py
    
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[INFO] Kiosk closed normally. Exiting loop." | tee -a "$LOG_FILE"
        break
    fi
    
    echo "[ERROR] Kiosk crashed with code $EXIT_CODE. Restarting in 5s..." | tee -a "$LOG_FILE"
    sleep 5
done
