@echo off
echo ============================================
echo    SUNDAY Voice Assistant - Build Script
echo ============================================
echo.

REM Activate virtual environment
call envsunday\Scripts\activate.bat

REM Install PyInstaller if not present
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [BUILD] Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [BUILD] Starting PyInstaller build...
echo.

pyinstaller --clean sunday.spec

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo    BUILD SUCCESSFUL!
    echo    Output: dist\SUNDAY\SUNDAY.exe
    echo ============================================
    echo.
    echo To distribute, zip the entire dist\SUNDAY folder.
) else (
    echo.
    echo ============================================
    echo    BUILD FAILED! Check errors above.
    echo ============================================
)

pause
