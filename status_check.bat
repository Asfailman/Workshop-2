@echo off
title Check AI Guidance Backend Status
echo ==========================================================
echo Checking Backend & Ngrok Status...
echo ==========================================================

echo.
echo [1] Checking Port 8000 (FastAPI Backend):
powershell -NoProfile -Command "$conn = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue; if ($conn) { Write-Host '  >> RUNNING (Port 8000 active, PID: ' $conn.OwningProcess ')' -ForegroundColor Green } else { Write-Host '  >> NOT RUNNING (Port 8000 inactive)' -ForegroundColor Red }"

echo.
echo [2] Checking Ngrok Tunnel:
tasklist /fi "imagename eq ngrok.exe" | find /i "ngrok.exe" >nul
if %ERRORLEVEL% EQU 0 (
    echo   ^>^> RUNNING (ngrok.exe process active)
) else (
    echo   ^>^> NOT RUNNING
)

echo.
echo ==========================================================
pause

