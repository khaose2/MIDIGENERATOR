@echo off
REM Ultimate MIDI Generator - Complete Setup with Virtual Environment
REM This creates a virtual environment and installs all dependencies

echo.
echo ========================================
echo   Ultimate MIDI Generator - Full Setup
echo ========================================
echo.
echo This script will:
echo   1. Create a Python virtual environment
echo   2. Install all required packages
echo   3. Set up the MIDI generator for use
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    goto :error
)

echo Python found! Starting setup...
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment!
        goto :error
    )
) else (
    echo [1/4] Virtual environment already exists, using existing one...
)

REM Activate virtual environment
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment!
    goto :error
)

REM Upgrade pip
echo [3/4] Upgrading pip in virtual environment...
python -m pip install --upgrade pip

REM Install packages
echo [4/4] Installing packages in virtual environment...
echo.

echo Installing core MIDI library...
python -m pip install mido>=1.2.10

echo Installing game/audio library...
python -m pip install pygame>=2.1.0

echo Installing visualization libraries...
python -m pip install matplotlib>=3.5.0
python -m pip install numpy>=1.21.0
python -m pip install scipy>=1.7.0

echo Installing optional audio library...
python -m pip install pyaudio>=0.2.11
if %ERRORLEVEL% neq 0 (
    echo WARNING: PyAudio installation failed. This is optional.
)

REM Install from requirements if it exists
if exist requirements.txt (
    echo Installing from requirements.txt...
    python -m pip install -r requirements.txt
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Virtual environment created and packages installed!
echo.
echo To use the MIDI Generator:
echo.
echo Method 1 - Use the launcher:
echo   Double-click 'launch_venv.bat'
echo.
echo Method 2 - Manual activation:
echo   1. Run: venv\Scripts\activate.bat
echo   2. Run: python MIDI.PY
echo.
echo Method 3 - Direct run:
echo   venv\Scripts\python.exe MIDI.PY
echo.
echo Test installation:
echo   venv\Scripts\python.exe test_generator.py
echo.
goto :end

:error
echo.
echo ========================================
echo   Setup Failed!
echo ========================================
echo.
echo Please fix the above errors and try again.
echo You may need to:
echo   - Install Python from https://python.org
echo   - Run as administrator
echo   - Check your internet connection
echo.

:end
echo Press any key to exit...
pause >nul
