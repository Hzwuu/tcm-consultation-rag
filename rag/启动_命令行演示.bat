@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
set "PYTHONIOENCODING=utf-8"

if exist "%~dp0.venv\Scripts\python.exe" goto run
echo The local environment is not ready.
echo Installing Python if needed, then preparing the project environment...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0环境准备.ps1"
if errorlevel 1 goto failed

:run
echo Starting the TCM CLI demo...
"%~dp0.venv\Scripts\python.exe" -m tcm_agent.cli --demo
goto end

:failed
echo.
echo Environment setup failed. Check the network connection and try again.

:end
pause
