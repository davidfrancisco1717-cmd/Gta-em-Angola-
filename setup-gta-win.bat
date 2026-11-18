@echo off
cd /d "%~dp0"

if not exist "..\story\stories.json" (
  echo Erro: arquivo ..\story\stories.json nao encontrado.
  echo Mantenha a pasta setup dentro da pasta principal do jogo.
  pause
  exit /b 1
)

set NEED_INSTALL=0
if not exist ".venv\Scripts\python.exe" (
  set NEED_INSTALL=1
) else (
  ".venv\Scripts\python.exe" -c "import PySide6" >nul 2>nul
  if errorlevel 1 set NEED_INSTALL=1
)

if "%NEED_INSTALL%"=="1" (
  echo Ambiente ou dependencias ^(PySide6^) ainda nao instalados.
  set /p RESP="Deseja instalar agora? (S/N): "
  if /i not "%RESP%"=="S" (
    echo Instalacao cancelada. Execute install-win.bat quando desejar instalar.
    pause
    exit /b 1
  )
  where py >nul 2>nul
  if %errorlevel%==0 (
    py install.py
  ) else (
    python install.py
  )
  if errorlevel 1 (
    echo Falha durante a instalacao.
    pause
    exit /b 1
  )
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 (
  echo.
  echo O Setup encerrou com erro. Veja os detalhes acima.
  pause
  exit /b 1
)
