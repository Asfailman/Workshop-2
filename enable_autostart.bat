@echo off
title Enable Backend Auto-Start on Windows Login
echo ==========================================================
echo Adding AI Guidance Backend to Windows Startup...
echo ==========================================================

set "TARGET_SCRIPT=%~dp0start_hidden.vbs"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_FOLDER%\AIGuidance_Backend.lnk"

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%TARGET_SCRIPT%\"'; $s.WorkingDirectory = '%~dp0'; $s.Save()"

if exist "%SHORTCUT%" (
    echo.
    echo [SUCCESS] Auto-start enabled!
    echo The backend and ngrok will now launch silently in the background
    echo automatically whenever you turn on / log into your PC.
) else (
    echo.
    echo [ERROR] Failed to create shortcut in Startup folder.
)

echo.
echo ==========================================================
pause

