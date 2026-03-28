@echo off
REM ============================================================
REM run.bat — FlaskDjango App Windows Başlatma Betiği
REM Düzeltmeler:
REM   - src/src.run.bat olmayan referans kaldırıldı
REM   - continue=0 geçersiz sözdizimi kaldırıldı
REM   - Çakışan PYTHONPATH değişken atamaları temizlendi
REM   - Sistem gereksinim kontrolü eklendi
REM ============================================================

setlocal enabledelayedexpansion

REM ── Başlık ────────────────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   FlaskDjango App - Windows Baslatici
echo   Kullanici   : %USERNAME%
echo   Tarih/Saat  : %DATE% %TIME%
echo   Dizin       : %~dp0
echo  ============================================================
echo.

REM ── Python kontrolü ───────────────────────────────────────────────────────
echo  [--] Python kontrol ediliyor...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [!!] Python bulunamadi!
    echo  [!!] https://python.org/downloads adresinden Python 3.10+ kurun.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] Python %PY_VER%

REM ── pip kontrolü ──────────────────────────────────────────────────────────
echo  [--] pip kontrol ediliyor...
python -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [!!] pip bulunamadi - python -m ensurepip calistirin
    pause
    exit /b 1
)
echo  [OK] pip mevcut

REM ── Sanal ortam ───────────────────────────────────────────────────────────
echo  [--] Sanal ortam kontrol ediliyor...
if not exist "%~dp0.venv\" (
    echo  [--] .venv olusturuluyor...
    python -m venv "%~dp0.venv"
    if %ERRORLEVEL% neq 0 (
        echo  [!!] Sanal ortam olusturulamadi
        pause
        exit /b 1
    )
    echo  [OK] Sanal ortam olusturuldu
) else (
    echo  [OK] Mevcut .venv kullaniliyor
)

REM ── Aktivasyon ────────────────────────────────────────────────────────────
call "%~dp0.venv\Scripts\activate.bat"
echo  [OK] Sanal ortam aktive edildi

REM ── Bağımlılık kurulumu ───────────────────────────────────────────────────
if exist "%~dp0requirements_api.txt" (
    echo  [--] Bagimliliklar yukleniyor...
    python -m pip install -r "%~dp0requirements_api.txt" -q
    if %ERRORLEVEL% neq 0 (
        echo  [!!] Paket kurulumu basarisiz
        pause
        exit /b 1
    )
    echo  [OK] Bagimliliklar yuklendi
) else (
    echo  [??] requirements_api.txt bulunamadi - atlaniyor
)

REM ══════════════════════════════════════════════════════════════════════
REM  SİSTEM GEREKSİNİM KONTROL BLOĞU
REM ══════════════════════════════════════════════════════════════════════
echo.
echo  ============================================================
echo   SISTEM GEREKSINIM KONTROLU
echo  ============================================================

REM Python sürüm bilgisi
echo  [--] Platform bilgisi:
python -c "import platform, sys; print('      Python:', sys.version); print('      OS    :', platform.system(), platform.release()); print('      Mimari:', platform.machine())"

REM Disk alanı
echo  [--] Disk alani:
python -c "import shutil; d=shutil.disk_usage('.'); print(f'      Bos: {d.free//1024//1024:,} MB  |  Toplam: {d.total//1024//1024//1024} GB')"

REM Port kontrolü
echo  [--] Port kontrol:
python -c "import socket; ports=[5000,8000]; [print(f'      Port {p}: Bos' if socket.socket().connect_ex(('127.0.0.1',p))!=0 else f'      Port {p}: Kullanimda!') for p in ports]"

REM Paket kontrolü
echo  [--] Kritik paketler:
python -c "pkgs=[('flask','Flask'),('flask_sqlalchemy','Flask-SQLAlchemy'),('sqlalchemy','SQLAlchemy'),('jwt','PyJWT')]; [print(f'      [OK] {n}=={__import__(m).__version__}') if (lambda:__import__(m))() else None for m,n in pkgs]" 2>nul

REM syscheck.py varsa çalıştır
if exist "%~dp0syscheck.py" (
    echo.
    echo  [--] Detayli kontrol baslatiliyor (syscheck.py)...
    python "%~dp0syscheck.py" --quiet
) else (
    echo  [??] syscheck.py bulunamadi - atlaniyor
)

REM ══════════════════════════════════════════════════════════════════════
REM  UYGULAMAYI BAŞLAT
REM ══════════════════════════════════════════════════════════════════════
echo.
echo  ============================================================
echo   UYGULAMA BASLATILIYOR
echo  ============================================================

if not exist "%~dp0main.py" (
    echo  [!!] main.py bulunamadi!
    pause
    exit /b 1
)

echo  [OK] http://127.0.0.1:5000 adresinde aciliyor...
echo  [--] Durdurmak icin CTRL+C kullanin
echo.

python "%~dp0main.py"

REM ── Çıkış ─────────────────────────────────────────────────────────────────
echo.
echo  [--] Uygulama sonlandi.
echo  [--] Cikmak icin bir tusa basin...
pause >nul
endlocal