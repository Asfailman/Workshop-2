@echo off
title AI Guidance Backend Server

REM Activate virtual environment if present
if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
)

cd /d "%~dp0module_1_back_end"
echo ==================================================
echo Starting Backend Server on http://0.0.0.0:8000 ...
echo ==================================================
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
