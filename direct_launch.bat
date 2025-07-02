@echo off
REM Direct launch for MIDI Generator
REM Use this if the regular launch.bat doesn't work

echo ========================================
echo   Direct MIDI Generator Launch
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Run the Python application directly
python MIDI.PY

echo.
echo Application closed.
pause
