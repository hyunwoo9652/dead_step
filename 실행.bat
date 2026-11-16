@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 main.py
    if errorlevel 1 pause
    exit /b
)
where python >nul 2>nul
if not errorlevel 1 (
    python main.py
    if errorlevel 1 pause
    exit /b
)
echo Python이 필요합니다. https://www.python.org/downloads/ 에서 설치해 주세요.
echo 설치할 때 Tcl/Tk 구성요소를 포함하세요. 이후 다시 실행해 주세요.
pause
