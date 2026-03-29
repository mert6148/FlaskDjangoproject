@echo off
REM src_protection.bat - Basit sistem koruma scripti
SETLOCAL ENABLEDELAYEDEXPANSION

echo Proje koruma denetimi basliyor...
set PROJECT_DIR=%~dp0..
set BACKUP_DIR=%PROJECT_DIR%backup
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 1) Kritik dosyalarin varligini kontrol et
set MISSING=
for %%f in ("auth\main.py" "app\app.py" "docs\documentation.html" "index.html") do (
  if not exist "%PROJECT_DIR%%%f" (
    set MISSING=!MISSING! %%f
  )
)
if "!MISSING!" neq "" (
  echo Uyari: eksik dosyalar: !MISSING!
) else (
  echo Kritik dosyalar bulundu.
)

REM 2) Yedekleme
xcopy "%PROJECT_DIR%app\*.py" "%BACKUP_DIR%\app\" /Y /I >nul
xcopy "%PROJECT_DIR%auth\*.py" "%BACKUP_DIR%\auth\" /Y /I >nul
xcopy "%PROJECT_DIR%docs\*.html" "%BACKUP_DIR%\docs\" /Y /I >nul

echo Yedekleme tamamlandi: %BACKUP_DIR%

REM 3) Istemsiz .exe/dll kontrolu
for /R "%PROJECT_DIR%" %%g in (*.exe *.dll) do (
  echo Supheli dosya bulundu: %%g
)

echo Koruma islemi sonlandi.
pause