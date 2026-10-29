@echo off
echo ==========================================================
echo    SIGMA VTT - Startup Script v3.0.0
echo ==========================================================
echo.

echo [1/2] Starting Backend Server (Uvicorn - Port 8000)...
start "Sigma VTT Backend Server" /D "%~dp0backend" python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo [2/2] Starting Frontend UI (Vite - Port 3000)...
start "Sigma VTT Frontend UI" /D "%~dp0frontend" call npm run dev

echo.
echo Preparing browser...
timeout /t 4 /nobreak >nul
start http://localhost:3000

echo ==========================================================
echo   SIGMA VTT is now running successfully!
echo   - Frontend UI: http://localhost:3000
echo   - API docs (Swagger): http://localhost:8000/docs
echo ==========================================================
pause
