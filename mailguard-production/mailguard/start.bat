@echo off
echo.
echo  ╔══════════════════════════════════════╗
echo  ║   MailGuard — Email DNS Checker      ║
echo  ╚══════════════════════════════════════╝
echo.

python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)

echo [1/2] Installing dependencies...
pip install -r requirements.txt --quiet

echo [2/2] Starting MailGuard on http://localhost:5050
echo.
echo   Open: http://localhost:5050
echo   Stop: Ctrl+C
echo.

start "" timeout /t 2 >nul & start "" "http://localhost:5050"
python app.py
pause
