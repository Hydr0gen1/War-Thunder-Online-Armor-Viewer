@echo off
set ROOT=%~dp0
set ROOT=%ROOT:~0,-1%

echo Starting wt-armor-viewer...
echo Project root: %ROOT%

start "WT Backend"  cmd /k "cd /d "%ROOT%\backend" && python -m pip install -r requirements.txt && python -m uvicorn main:app --reload --port 8000"
timeout /t 3 /nobreak >nul
start "WT Frontend" cmd /k "cd /d "%ROOT%\frontend" && npm install --silent && npx vite"
