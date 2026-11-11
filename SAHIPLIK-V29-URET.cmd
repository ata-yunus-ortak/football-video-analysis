@echo off
rem Possession v2.9 (submission system): generate the file locally from the provided bundle (never upload the data).
rem v2.5b + published second-half kick-off + player-registered broadcast ball; uses the clock readings of SAAT-OKU.cmd when present (see run.json).
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
set "OUT=%USERPROFILE%\FootballPrivate\possession-v29-run-%STAMP%"
set "CLK=%USERPROFILE%\FootballPrivate\possession-clock"
set CLOCKARGS=
if exist "%CLK%\tactical\observations.jsonl" if exist "%CLK%\broadcast\observations.jsonl" set CLOCKARGS=--tactical-clock "%CLK%\tactical" --broadcast-clock "%CLK%\broadcast"
"%PY%" -m possession.run29 --data-dir "%MTAH_DATA_DIR%" --out "%OUT%" %CLOCKARGS%
if errorlevel 1 (pause & exit /b 1)
"%PY%" -m possession.validate "%OUT%\submission.csv"
"%PY%" -m possession.plausibility "%OUT%\submission.csv"
if errorlevel 1 echo UYARI: Makulluk kontrolunde FAIL var. Gondermeden once hangi satirin FAIL oldugunu bildirin.
echo.
echo Cikti: %OUT%\submission.csv
pause
