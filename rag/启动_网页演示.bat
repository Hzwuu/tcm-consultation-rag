@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
set "PYTHONIOENCODING=utf-8"

if exist "%~dp0.venv\Scripts\python.exe" goto verify

:prepare
echo The local environment is not ready.
echo Installing Python if needed, then installing project dependencies...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0环境准备.ps1"
if errorlevel 1 goto failed
goto run

:verify
"%~dp0.venv\Scripts\python.exe" -c "import streamlit" >nul 2>nul
if errorlevel 1 goto prepare

:run
echo Starting the web demo...
echo Keep this window open while presenting.
"%~dp0.venv\Scripts\python.exe" -m streamlit run app\streamlit_app.py
goto end

:failed
echo.
echo Environment setup failed. Check the network connection and try again.

:end
pause
