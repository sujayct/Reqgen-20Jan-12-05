@echo off
REM ==========================================
REM ReqGen Complete System Startup Script
REM Windows Batch File
REM ==========================================
REM
REM This script will start all required services for ReqGen
REM Required: Node.js, Python, MySQL running
REM
REM Usage: Double-click this file or run from command prompt
REM        It will open 3 terminals automatically
REM

cd /d "c:\Users\sujay.palande\Downloads\Reqgen 20Jan-12-05"

echo.
echo ====================================================
echo     ReqGen System Startup Script
echo ====================================================
echo.

REM Check if MySQL is running
echo Checking MySQL...
netstat -ano | findstr :3306 >nul
if errorlevel 1 (
    echo.
    echo [!] MySQL not detected on port 3306
    echo [*] Please start XAMPP MySQL or MySQL service first
    echo.
    pause
)

REM Terminal 1: Node Backend
echo.
echo [1] Opening Node.js Backend Terminal...
start "ReqGen Node Backend (5027)" cmd /k "title Node Backend - npm run dev && npm run dev"

timeout /t 3 /nobreak

REM Terminal 2: Python Backend
echo.
echo [2] Opening Python Backend Terminal...
start "ReqGen Python Backend (5000)" cmd /k "cd python-backend && title Python Backend - python app.py && venv\Scripts\activate && python app.py"

timeout /t 3 /nobreak

REM Terminal 3: Status Monitor
echo.
echo [3] Opening Status Monitor Terminal...
start "ReqGen Status Monitor" cmd /k "title ReqGen Status Monitor && cls && echo. && echo === ReqGen Services === && echo. && echo Node Backend: http://localhost:5027 && echo Python Backend: http://localhost:5000 && echo Frontend: http://localhost:5173 && echo. && echo Waiting for services to start (30 seconds)... && timeout /t 30 /nobreak && cls && echo. && echo [CHECKING SERVICES] && echo. && (curl -s http://localhost:5027/api/health >nul && echo [OK] Node Backend is responding) || echo [FAIL] Node Backend not responding && (curl -s http://localhost:5000/api/health >nul && echo [OK] Python Backend is responding) || echo [FAIL] Python Backend not responding && echo. && echo Open browser: http://localhost:5173 && echo. && echo To stop all services: Close all terminal windows && pause"

REM Open browser
timeout /t 5 /nobreak
echo.
echo [4] Opening browser...
start http://localhost:5173

echo.
echo ====================================================
echo Services starting... Check the opened terminals
echo ====================================================
echo.
echo Expected outputs:
echo   Terminal 1: "Server running on port 5027"
echo   Terminal 2: "Running on http://localhost:5000"
echo   Terminal 3: Service health check status
echo.
echo Browser should open automatically to: http://localhost:5173
echo.
echo If services don't start:
echo   1. Check that Node.js and Python are installed
echo   2. Check TROUBLESHOOTING_ERRORS.md for help
echo.
echo To stop everything: Close all terminal windows
echo.
pause
