@echo off
TITLE Museum Kiosk - Launcher
CLS

echo ==========================================
echo    MUSEUM KIOSK - GESTURE CONTROL
echo ==========================================
echo.
echo  1. Run Kiosk (Fullscreen)
echo  2. Run Kiosk (Windowed + Debug)
echo  3. Run Admin Panel (Web)
echo  4. Install/Update Dependencies
echo  5. Exit
echo.
set /p choice="Select an option (1-5): "

if "%choice%"=="1" goto run_kiosk
if "%choice%"=="2" goto run_debug
if "%choice%"=="3" goto run_admin
if "%choice%"=="4" goto install_reqs
if "%choice%"=="5" exit
goto start

:run_kiosk
echo [INFO] Starting Kiosk...
python main.py
goto end

:run_debug
echo [INFO] Starting Kiosk in Windowed Debug mode...
python main.py --windowed --debug
goto end

:run_admin
echo [INFO] Starting Admin Panel...
echo [INFO] Access via http://localhost:5000
python main.py --admin
goto end

:install_reqs
echo [INFO] Installing dependencies...
python -m pip install -r requirements.txt
echo [INFO] Installation finished.
pause
goto start

:end
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] The application exited with an error.
    pause
)
exit
