@echo off
REM Windows launcher (double-click or run from Command Prompt / PowerShell).
REM   scripts\start.bat          run the monolith  (http://localhost:8000)
REM   scripts\start.bat micro    run the microservices (gateway + query + data + history + chart)
REM Optional: set QUERYX_HOST=0.0.0.0 to allow other devices on your network, QUERYX_PORT=8000
cd /d "%~dp0.."

if not exist .venv (
  python -m venv .venv
  if errorlevel 1 (
    echo Could not create a virtual environment. Install Python 3.10+ from python.org and tick "Add Python to PATH".
    exit /b 1
  )
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt

if /I "%1"=="micro" goto micro
if "%QUERYX_HOST%"=="" set QUERYX_HOST=127.0.0.1
if "%QUERYX_PORT%"=="" set QUERYX_PORT=8000
python -m uvicorn app.main:app --host %QUERYX_HOST% --port %QUERYX_PORT%
goto end

:micro
python scripts\run_microservices.py

:end
