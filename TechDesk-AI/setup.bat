@echo off
title TechDesk AI Setup
echo ========================================================
echo Installing TechDesk AI Environment and Packages...
echo ========================================================

cd /d "%~dp0"

set PYTHON_CMD=python
python --version >nul 2>nul
if ERRORLEVEL 1 (
    where py >nul 2>nul
    if ERRORLEVEL 1 (
        echo [ERROR] Python was not found. Install Python 3.10+ and enable the Python launcher.
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
)

echo [1/3] Creating Python virtual environment in .venv ...
%PYTHON_CMD% -m venv .venv
if ERRORLEVEL 1 (
    echo [ERROR] Could not create the virtual environment.
    pause
    exit /b 1
)

echo [2/3] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/3] Installing requirements from requirements.txt ...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if ERRORLEVEL 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo Setup Complete!
echo You can now double-click run.bat to start the server!
echo ========================================================
pause
