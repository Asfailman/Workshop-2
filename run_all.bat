@echo off
title Launch AI Guidance Backend and Ngrok
echo ==========================================================
echo Starting AI Guidance Backend and Ngrok Tunnel...
echo ==========================================================

REM Start the backend in a new command window
start "Backend Server" cmd /c "call "%~dp0run_backend.bat""

REM Wait 3 seconds for the backend to initialize
timeout /t 3 /nobreak >nul

REM Start ngrok tunnel in a new command window
start "Ngrok Tunnel" cmd /c "call "%~dp0run_ngrok.bat""

echo Done! Both servers are launching in separate windows.
