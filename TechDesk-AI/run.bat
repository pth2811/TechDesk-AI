@echo off
title TechDesk AI Server
echo ========================================================
echo Starting TechDesk AI Enterprise Service Desk...
echo ========================================================

cd /d "%~dp0"

set PYTHON_CMD=python

IF EXIST ".venv\Scripts\python.exe" (
    echo [OK] Using local virtual environment .venv
    set PYTHON_CMD=.venv\Scripts\python.exe
) ELSE (
    echo [INFO] No local .venv found. Attempting system python...
    python --version >nul 2>nul
    IF ERRORLEVEL 1 (
        where py >nul 2>nul
        IF NOT ERRORLEVEL 1 (
            set PYTHON_CMD=py
        ) ELSE (
            echo [ERROR] Python was not found. Run setup.bat after installing Python 3.10+.
            pause
            exit /b 1
        )
    )
)

echo Starting FastAPI server on http://127.0.0.1:8001 ...
echo Press Ctrl+C anytime to stop the server.
echo.

%PYTHON_CMD% -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

if ERRORLEVEL 1 (
    echo.
    echo [ERROR] Server failed to start.
    echo If dependencies are missing, please run:
    echo     python -m venv .venv
    echo     .venv\Scripts\activate
    echo     pip install -r requirements.txt
    echo.
)

pause
