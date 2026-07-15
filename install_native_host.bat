@echo off
setlocal
if "%~1"=="" (
  echo Copy the extension ID from edge://extensions, then run:
  echo install_native_host.bat ^<EDGE_EXTENSION_ID^>
  exit /b 2
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_native_host.ps1" "%~1"
exit /b %errorlevel%
