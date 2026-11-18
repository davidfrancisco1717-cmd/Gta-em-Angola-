@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py install.py
) else (
  python install.py
)
echo.
pause
