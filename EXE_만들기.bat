@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m venv .build-env
) else (
    python -m venv .build-env
)
if errorlevel 1 goto failed
.build-env\Scripts\python.exe -m pip install pyinstaller
if errorlevel 1 goto failed
.build-env\Scripts\python.exe -m PyInstaller --clean --noconfirm --onefile --windowed --name DeadStep --add-data "web_ui.html;." main.py
if errorlevel 1 goto failed
echo 완료: dist\DeadStep.exe
pause
exit /b
:failed
echo 생성 실패. 위 오류 메시지를 확인하세요.
pause
exit /b 1
