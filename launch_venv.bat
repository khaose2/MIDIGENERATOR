@echo off
REM Ultimate MIDI Generator Launcher with Virtual Environment Support
REM This batch file launches the MIDI Generator using the virtual environment

echo.
echo ========================================
echo   Ultimate MIDI Generator - Fun Tool
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if exist "venv\Scripts\python.exe" (
    echo Using virtual environment...
    echo Starting MIDI Generator...
    echo.
    venv\Scripts\python.exe MIDI.PY
) else if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment (.venv)...
    echo Starting MIDI Generator...
    echo.
    .venv\Scripts\python.exe MIDI.PY
) else (
    echo No virtual environment found, using system Python...
    echo Starting MIDI Generator...
    echo.
    python MIDI.PY
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo ========================================
    echo   Error occurred!
    echo ========================================
    echo.
    echo The MIDI Generator failed to start.
    echo This might be because:
    echo   1. Dependencies are not installed
    echo   2. Python is not installed
    echo   3. Virtual environment is corrupted
    echo.
    echo Solutions:
    echo   1. Run 'install_dependencies.bat' to install packages
    echo   2. Run 'setup_venv.bat' to create a virtual environment
    echo   3. Install Python from https://python.org
    echo.
)

echo.
echo Application closed.
echo Press any key to exit...
pause >nul
