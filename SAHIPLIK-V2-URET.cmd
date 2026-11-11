@echo off
rem Possession v2: generate the submission locally from the provided bundle (never upload the data).
chcp 65001 >nul
cd /d "%~dp0"
if exist "%~dp0viewer-local.cmd" call "%~dp0viewer-local.cmd"
if not defined MTAH_DATA_DIR set "MTAH_DATA_DIR=%USERPROFILE%\FootballPrivate\mtah2027\bundle"
if not exist "%MTAH_DATA_DIR%\tactical\BAR-ATH_tactical_atd.xml" (
  echo Veri bulunamadi: %MTAH_DATA_DIR%\tactical\BAR-ATH_tactical_atd.xml
  echo viewer-local.example.cmd dosyasini viewer-local.cmd olarak kopyalayip MTAH_DATA_DIR yolunu ayarlayin.
  pause
  exit /b 1
)
set "PY=python"
if exist "%~dp0.venv-possession\Scripts\python.exe" set "PY=%~dp0.venv-possession\Scripts\python.exe"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%i"
set "OUT=%USERPROFILE%\FootballPrivate\possession-v2-run-%STAMP%"
"%PY%" -m possession.run --data-dir "%MTAH_DATA_DIR%" --out "%OUT%"
if errorlevel 1 (pause & exit /b 1)
"%PY%" -m possession.validate "%OUT%\submission.csv"
echo.
echo Cikti: %OUT%\submission.csv
pause
