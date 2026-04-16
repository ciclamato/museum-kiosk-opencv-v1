@echo off
echo [INFO] Starting Museum Kiosk Admin Panel...
echo [INFO] Once running, open http://localhost:5000 in your browser.
echo.
python main.py --admin
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Admin panel failed to start. Ensure Python is installed.
    pause
)
