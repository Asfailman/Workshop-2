@echo off
title Stop AI Guidance Backend and Ngrok
echo ==========================================================
echo Stopping AI Guidance Backend (Port 8000) and Ngrok...
echo ==========================================================

REM Stop process using Port 8000 (Backend / Uvicorn)
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force; Write-Host 'Stopped backend process (PID: ' $_.OwningProcess ')' }"

REM Stop Ngrok process
taskkill /F /IM ngrok.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Stopped ngrok.exe.
) else (
    echo Ngrok was not running.
)

echo.
echo All services stopped successfully!
echo ==========================================================
pause

