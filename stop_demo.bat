@echo off
setlocal
chcp 65001 >nul
title AI Job Copilot 2.0 - Stop Docker Demo

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_demo.ps1"
set "exit_code=%ERRORLEVEL%"

echo.
pause
exit /b %exit_code%
