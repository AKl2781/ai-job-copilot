@echo off
setlocal
chcp 65001 >nul
title Install AI Job Copilot Autostart

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_autostart.ps1"
set "exit_code=%ERRORLEVEL%"

echo.
pause
exit /b %exit_code%
