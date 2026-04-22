#!/bin/bash
# setup_kiosk.sh
# Script de instalación automática para el Museo Kiosk en Raspberry Pi 4
# Ejecutar con: bash tools/setup_kiosk.sh

echo "================================================================"
echo "🚀 INICIANDO INSTALACIÓN AUTOMÁTICA DEL KIOSCO (RASPBERRY PI) 🚀"
echo "================================================================"

# 1. Actualizar e instalar dependencias del sistema
echo "[1/5] Actualizando sistema e instalando dependencias (OpenCV, Pygame, etc)..."
sudo apt update
sudo apt install -y python3-venv python3-pip libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev rpi-connect git x11-xserver-utils unclutter

# 2. Configurar entorno virtual y dependencias de Python
echo "[2/5] Configurando entorno virtual de Python..."
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1 && pwd)"
cd "$DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv --system-site-packages
fi

echo "[3/5] Instalando dependencias de Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Ocultar el cursor del mouse a nivel de sistema operativo
echo "[4/5] Ocultando cursor del mouse del sistema..."
sudo sed -i 's/xserver-command=X/xserver-command=X -nocursor/' /etc/lightdm/lightdm.conf 2>/dev/null || true

# 4. Crear el servicio para que arranque automático al prender
echo "[5/5] Creando servicio de Auto-Arranque (Systemd)..."
SERVICE_FILE="/etc/systemd/system/museum-kiosk.service"

sudo bash -c "cat > $SERVICE_FILE" << EOL
[Unit]
Description=Museum Kiosk OpenCV
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
User=$USER
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER/.Xauthority
WorkingDirectory=$DIR
ExecStart=$DIR/venv/bin/python $DIR/main.py --windowed
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable museum-kiosk.service

echo "================================================================"
echo "✅ INSTALACIÓN COMPLETADA EXITOSAMENTE ✅"
echo "================================================================"
echo "-> El programa arrancará automáticamente cada vez que enciendas la Raspberry Pi."
echo "-> Si quieres arrancarlo ahora mismo, ejecuta:"
echo "   sudo systemctl start museum-kiosk.service"
echo ""
echo "-> Para usar Pi Connect (acceso remoto), recuerda ejecutar:"
echo "   rpi-connect signin"
echo "================================================================"
