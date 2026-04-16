@echo off
TITLE Museum Kiosk - Dependency Installer
echo ==============================================
echo    MUSEUM KIOSK - Dependency Installer
echo ==============================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found.
    echo Please install Python 3.8 or higher from python.org and ensure 'Add to PATH' is checked.
    echo.
    pause
    exit /b
)

echo [INFO] Updating pip...
python -m pip install --upgrade pip

echo [INFO] Installing required packages from requirements.txt...
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed. 
    echo Please check your internet connection and ensure requirements.txt is in this folder.
    echo.
    pause
    exit /b
)

echo.
echo ==============================================
echo [SUCCESS] Dependencies installed successfully.
echo.
echo You can now run the kiosk using:
echo  - launcher.bat (Menu)
echo  - run_kiosk.bat (Direct)
echo ==============================================
echo.
pause
