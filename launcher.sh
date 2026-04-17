#!/usr/bin/env bash
set -u

cd "$(dirname "$0")"

while true; do
  clear
  cat <<'EOF'
==========================================
   MUSEUM KIOSK - GESTURE CONTROL
==========================================

  1. Run Kiosk (Fullscreen)
  2. Run Kiosk (Windowed + Debug)
  3. Run Admin Panel (Web)
  4. Install/Update Dependencies
  5. Exit
EOF

  printf '\nSelect an option (1-5): '
  read -r choice

  case "$choice" in
    1)
      echo "[INFO] Starting Kiosk..."
      python3 main.py || {
        echo
        echo "[ERROR] The application exited with an error."
        read -r -p "Press Enter to continue..."
      }
      ;;
    2)
      echo "[INFO] Starting Kiosk in Windowed Debug mode..."
      python3 main.py --windowed --debug || {
        echo
        echo "[ERROR] The application exited with an error."
        read -r -p "Press Enter to continue..."
      }
      ;;
    3)
      echo "[INFO] Starting Admin Panel..."
      echo "[INFO] Access via http://localhost:5000"
      python3 main.py --admin || {
        echo
        echo "[ERROR] The application exited with an error."
        read -r -p "Press Enter to continue..."
      }
      ;;
    4)
      ./install_requirements.sh || true
      read -r -p "Press Enter to continue..."
      ;;
    5)
      exit 0
      ;;
    *)
      echo "[ERROR] Invalid option."
      read -r -p "Press Enter to continue..."
      ;;
  esac
done
