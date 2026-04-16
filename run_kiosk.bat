@echo off
echo [INFO] Starting Museum Kiosk...
echo.
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Kiosk crashed or Python is not installed.
    pause
)
