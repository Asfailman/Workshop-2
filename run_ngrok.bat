@echo off
title Ngrok Tunnel (AI Guidance Backend)
echo ==========================================================
echo Starting Ngrok Tunnel for AI Guidance Backend (Port 8000)...
echo ==========================================================

REM Attempt to connect with project domain:
ngrok http --url=dazzling-endurance-huddle.ngrok-free.dev 8000
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Default custom domain not available on this ngrok account.
    echo Starting standard tunnel on port 8000...
    ngrok http 8000
)
pause
