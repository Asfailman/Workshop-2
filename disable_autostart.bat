@echo off
title Disable Backend Auto-Start
echo ==========================================================
echo Removing AI Guidance Backend from Windows Startup...
echo ==========================================================

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_FOLDER%\AIGuidance_Backend.lnk"

if exist "%SHORTCUT%" (
    del /f /q "%SHORTCUT%"
    echo.
    echo [SUCCESS] Auto-start disabled!
    echo Shortcut removed from Startup folder.
) else (
    echo.
    echo Auto-start is already disabled (no shortcut found in Startup folder).
)

echo.
echo ==========================================================
pause

