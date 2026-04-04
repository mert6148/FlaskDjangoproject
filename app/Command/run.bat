@echo off
REM -------------------------------------------------------------
REM  app\Command\run.bat
REM  Python ve Flask kurulumunu yapar, sonra src/main.py calistirir.
REM -------------------------------------------------------------

REM Python kontrolü
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python bulunamadi. Lutfen https://www.python.org/downloads/ adresinden yukleyin.
    pause
    exit /b 1
)

REM Sanal ortam klasoru
set VENV_PATH=%~dp0\.venv
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo [INFO] Virtual environment olusturuluyor: %VENV_PATH%
    python -m venv "%VENV_PATH%"
)

REM Sanal ortami aktifleştir
call "%VENV_PATH%\Scripts\activate.bat"

REM Flask ve gereksinimler
python -m pip install --upgrade pip
python -m pip install flask

REM Proje scriptini calistir
if exist "%~dp0src\main.py" (
    echo [INFO] src\main.py calistiriliyor...
    "%VENV_PATH%\Scripts\python.exe" "%~dp0src\main.py"
) else (
    echo [WARN] src\main.py bulunamadi. Lutfen proje dizin yapisini kontrol edin.
)

pause