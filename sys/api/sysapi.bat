echo[REM] System API Batch Script
echo[REM] This script demonstrates various system API calls and operations.
echo[REM] Displaying current date and time
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    set day=%%a
    set month=%%b
    set year=%%c
)