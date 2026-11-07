@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "%~dp0viewer-local.cmd" call "%~dp0viewer-local.cmd"
if not defined MTAH_ALIGNMENT set "MTAH_ALIGNMENT=%USERPROFILE%\FootballPrivate\video-sync\alignment.json"
if not exist "%MTAH_ALIGNMENT%" (
  echo Otomatik esleme dosyasi bulunamadi. viewer-local.cmd icinde MTAH_ALIGNMENT yolunu ayarlayin.
  pause
  exit /b 1
)
python -m tools.paired_viewer --alignment "%MTAH_ALIGNMENT%" --port 8768 --open
if errorlevel 1 pause
