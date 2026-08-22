@echo off
title MykoKnoks Installer
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-MykoKnoks.ps1"
if errorlevel 1 (
  echo.
  echo Installation stopped with an error.
  echo Copy the error message or take a screenshot and send it to ChatGPT.
  echo.
  pause
  exit /b 1
)
exit /b 0
