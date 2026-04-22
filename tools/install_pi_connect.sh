#!/bin/bash
# Script to install Raspberry Pi Connect on Raspberry Pi OS.
# For more info: https://www.raspberrypi.com/documentation/services/connect.html

echo "[INFO] Installing Raspberry Pi Connect..."

# Update package lists
sudo apt update

# Install Raspberry Pi Connect
sudo apt install -y rpi-connect

echo "[INFO] Raspberry Pi Connect installed."
echo "[INFO] To sign in, run: rpi-connect signin"
echo "[INFO] Then follow the instructions to link your device."
