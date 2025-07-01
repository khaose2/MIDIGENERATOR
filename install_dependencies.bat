@echo off
REM Ultimate MIDI Generator - Dependencies Installer
REM This batch file installs all required Python packages

echo.
echo ========================================
echo   Ultimate MIDI Generator Setup
echo ========================================
echo.
echo Installing Python dependencies...
echo This may take a few minutes...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    goto :error
)

echo Python found! Installing packages...
echo.

REM Upgrade pip first
echo [1/8] Upgrading pip...
python -m pip install --upgrade pip

REM Install core MIDI libraries
echo [2/8] Installing MIDI library (mido)...
python -m pip install mido>=1.2.10

echo [3/8] Installing game library (pygame)...
python -m pip install pygame>=2.1.0

REM Install visualization libraries
echo [4/8] Installing plotting library (matplotlib)...
python -m pip install matplotlib>=3.5.0

echo [5/8] Installing numerical library (numpy)...
python -m pip install numpy>=1.21.0

echo [6/8] Installing scientific library (scipy)...
python -m pip install scipy>=1.7.0

echo [7/8] Installing audio analysis library (librosa)...
python -m pip install librosa

REM Optional audio library (may fail on some systems)
echo [8/8] Installing audio library (pyaudio - optional)...
python -m pip install pyaudio>=0.2.11
if %ERRORLEVEL% neq 0 (
    echo WARNING: PyAudio installation failed. This is optional for basic functionality.
    echo You can continue without it, but some audio features may not work.
)

REM Install from requirements.txt as backup
echo [9/9] Installing any remaining packages from requirements.txt...
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo requirements.txt not found, skipping...
)

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo All dependencies have been installed successfully!
echo.
echo Next steps:
echo   1. Run 'python MIDI.PY' to start the MIDI Generator
echo   2. Or double-click 'launch.bat' for easy startup
echo   3. Or run 'python test_generator.py' to test functionality
echo.
echo If you encounter any issues:
echo   - Make sure Python 3.7+ is installed
echo   - Try running as administrator
echo   - Check your internet connection
echo.
goto :end

:error
echo.
echo ========================================
echo   Installation Failed!
echo ========================================
echo.
echo Please fix the above errors and try again.
echo.

:end
echo Press any key to exit...
pause >nul
