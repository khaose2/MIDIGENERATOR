@echo off
REM Ultimate MIDI Generator Launcher
REM This batch file launches the MIDI Generator application

echo.
echo ========================================
echo   Ultimate MIDI Generator - Fun Tool
echo ========================================
echo.
echo Starting the application...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Run the Python application
python MIDI.PY

echo.
echo Application closed.
pause
