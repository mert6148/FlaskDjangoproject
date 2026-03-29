@echo off
REM run.bat — Sistem Başlatıcı
REM Düzeltmeler: run%data% geçersiz değişken ve echo( hatalı sözdizimi kaldırıldı

setlocal
echo  ================================
echo  ============= SRC ==============
echo  ================================
echo  Kullanici : %USERNAME%
echo  Tarih     : %DATE%  Saat: %TIME%
echo  Dizin     : %~dp0
echo  ================================

if not exist "%~dp0src\index.js" (
    echo  [!!] src\index.js bulunamadi
    pause & exit /b 1
)

where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [!!] Node.js bulunamadi - https://nodejs.org
    pause & exit /b 1
)

echo  [OK] Node.js: & node --version
echo  [--] Baslatiliyor...
node "%~dp0src\index.js"

echo  [--] Tamamlandi. Cikmak icin bir tusa basin.
pause >nul
endlocal