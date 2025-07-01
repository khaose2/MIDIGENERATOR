@echo off
REM Dependencies Test Script
REM This script tests if all required packages are installed correctly

echo.
echo ========================================
echo   Testing MIDI Generator Dependencies
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Determine which Python to use
set PYTHON_CMD=python
if exist "venv\Scripts\python.exe" (
    set PYTHON_CMD=venv\Scripts\python.exe
    echo Using virtual environment Python...
) else if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
    echo Using .venv virtual environment Python...
) else (
    echo Using system Python...
)

echo.
echo Testing Python installation...
%PYTHON_CMD% --version
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found!
    goto :error
)

echo.
echo Testing required packages...
echo.

echo [1/6] Testing mido (MIDI library)...
%PYTHON_CMD% -c "import mido; print('✓ mido version:', mido.version_info)"
if %ERRORLEVEL% neq 0 (
    echo ✗ mido not installed or not working
    set HAS_ERROR=1
) else (
    echo ✓ mido working correctly
)

echo.
echo [2/6] Testing pygame (audio/game library)...
%PYTHON_CMD% -c "import pygame; print('✓ pygame version:', pygame.version.ver)"
if %ERRORLEVEL% neq 0 (
    echo ✗ pygame not installed or not working
    set HAS_ERROR=1
) else (
    echo ✓ pygame working correctly
)

echo.
echo [3/6] Testing matplotlib (plotting library)...
%PYTHON_CMD% -c "import matplotlib; print('✓ matplotlib version:', matplotlib.__version__)"
if %ERRORLEVEL% neq 0 (
    echo ✗ matplotlib not installed or not working
    set HAS_ERROR=1
) else (
    echo ✓ matplotlib working correctly
)

echo.
echo [4/6] Testing numpy (numerical library)...
%PYTHON_CMD% -c "import numpy; print('✓ numpy version:', numpy.__version__)"
if %ERRORLEVEL% neq 0 (
    echo ✗ numpy not installed or not working
    set HAS_ERROR=1
) else (
    echo ✓ numpy working correctly
)

echo.
echo [5/6] Testing tkinter (GUI library)...
%PYTHON_CMD% -c "import tkinter; print('✓ tkinter working')"
if %ERRORLEVEL% neq 0 (
    echo ✗ tkinter not installed or not working
    set HAS_ERROR=1
) else (
    echo ✓ tkinter working correctly
)

echo.
echo [6/6] Testing MIDI generator import...
%PYTHON_CMD% -c "import sys; sys.path.append('.'); import MIDI; print('✓ MIDI generator can be imported')"
if %ERRORLEVEL% neq 0 (
    echo ✗ MIDI generator cannot be imported
    set HAS_ERROR=1
) else (
    echo ✓ MIDI generator ready to use
)

echo.
echo ========================================
if defined HAS_ERROR (
    echo   Some Dependencies Missing!
    echo ========================================
    echo.
    echo Some required packages are not installed or not working.
    echo.
    echo To fix this:
    echo   1. Run 'install_dependencies.bat' to install missing packages
    echo   2. Or run 'setup_venv.bat' to create a clean virtual environment
    echo   3. Make sure you have Python 3.7+ installed
    echo.
) else (
    echo   All Dependencies OK!
    echo ========================================
    echo.
    echo All required packages are installed and working!
    echo.
    echo You can now:
    echo   1. Run 'python MIDI.PY' or double-click 'launch.bat'
    echo   2. Run 'python test_generator.py' to test functionality
    echo   3. Start creating amazing MIDI music!
    echo.
)

goto :end

:error
echo.
echo ========================================
echo   Critical Error!
echo ========================================
echo.
echo Python is not installed or not accessible.
echo Please install Python 3.7+ from https://python.org
echo Make sure to check "Add Python to PATH" during installation.
echo.

:end
echo Press any key to exit...
pause >nul
