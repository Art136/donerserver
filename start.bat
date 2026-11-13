@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [burger] Первый запуск: создаю виртуалку и ставлю зависимости...
    python -m venv .venv
    if errorlevel 1 (
        echo [burger] Не нашёл python. Поставь Python 3.11+ и попробуй снова.
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo.
echo [burger] Сервер поднимается: http://127.0.0.1:8000
echo [burger] Остановить: Ctrl+C
echo.

".venv\Scripts\python.exe" main.py

pause
