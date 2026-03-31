@echo off
REM Windows test ve kurulum kodunu calistirir.
set SCRIPT_DIR=%~dp0

REM PowerShell ile kurulum scriptini calistir.
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& '%SCRIPT_DIR%windows_install.ps1'"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] windows_install.ps1 calistirilirken hata olustu.
    exit /b %ERRORLEVEL%
)

echo [INFO] Windows test hazirlama tamamlandi.
pause
