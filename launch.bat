@echo off
REM Ultimate MIDI Generator Launcher
REM This batch file launches the MIDI Generator application
setlocal

REM Check if Python is available in PATH
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not found in your PATH.
    echo Please install Python or set it in your PATH.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Ultimate MIDI Generator - Professional Edition
echo ========================================
echo.
echo Starting the application...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Run the launcher script instead of directly running MIDI.PY
python launch_midi_generator.py

echo.
echo Application closed.
pause
