@echo off
echo Starting MIDI Generator with MP3 to MIDI Conversion...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or later
    pause
    exit /b 1
)

REM Check if required modules are available
echo Checking dependencies...
python -c "import librosa, soundfile, numpy, scipy, mido, pygame, tkinter, matplotlib" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Some dependencies are missing. Installing now...
    pip install librosa soundfile numpy scipy mido pygame matplotlib
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies
        echo Please run: pip install librosa soundfile numpy scipy mido pygame matplotlib
        pause
        exit /b 1
    )
)

echo.
echo Dependencies OK! Starting MIDI Generator...
echo.

REM Start the main application
python MIDI.PY

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start MIDI Generator
    pause
)
